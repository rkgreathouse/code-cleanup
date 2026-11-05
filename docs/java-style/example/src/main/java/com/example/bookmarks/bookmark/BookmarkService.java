package com.example.bookmarks.bookmark;

import com.example.bookmarks.Settings;
import com.example.bookmarks.errors.ConflictException;
import com.example.bookmarks.errors.InvalidRequestException;
import com.example.bookmarks.errors.NotFoundException;
import java.time.Clock;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

@Service
public class BookmarkService {

  private static final Logger log = LoggerFactory.getLogger(BookmarkService.class);

  private final BookmarkRepository repository;
  private final Settings settings;
  private final Clock clock;

  public BookmarkService(BookmarkRepository repository, Settings settings, Clock clock) {
    this.repository = repository;
    this.settings = settings;
    this.clock = clock;
  }

  public Bookmark addBookmark(BookmarkRequest request) {
    if (request.tags().size() > settings.maxTags()) {
      throw new InvalidRequestException(
          "at most " + settings.maxTags() + " tags, got " + request.tags().size());
    }

    // the same page saved twice is one bookmark; the second save is a client mistake
    if (repository.findByUrl(request.url()).isPresent()) {
      throw new ConflictException("already bookmarked: " + request.url());
    }

    var bookmark = repository.save(request, clock.instant());
    log.info("added bookmark {} for {}", bookmark.id(), bookmark.url());
    return bookmark;
  }

  public Bookmark findBookmark(long id) {
    return repository.findById(id).orElseThrow(() -> new NotFoundException("no bookmark " + id));
  }

  public List<Bookmark> listBookmarks(String tag, int page) {
    var start = page * settings.pageSize();
    var matching = tag == null ? repository.findAll() : findTagged(tag);

    if (start >= matching.size()) {
      return List.of();
    }

    var end = Math.min(start + settings.pageSize(), matching.size());
    return matching.subList(start, end);
  }

  public void removeBookmark(long id) {
    if (!repository.delete(id)) {
      throw new NotFoundException("no bookmark " + id);
    }

    log.info("removed bookmark {}", id);
  }

  private List<Bookmark> findTagged(String tag) {
    return repository.findAll().stream().filter(bookmark -> bookmark.hasTag(tag)).toList();
  }
}
