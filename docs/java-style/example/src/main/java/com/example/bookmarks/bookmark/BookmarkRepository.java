package com.example.bookmarks.bookmark;

import java.time.Instant;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;
import org.springframework.stereotype.Repository;

@Repository
public class BookmarkRepository {

  private final Map<Long, Bookmark> bookmarks = new ConcurrentHashMap<>();
  private final AtomicLong nextId = new AtomicLong(1);

  public Bookmark save(BookmarkRequest request, Instant createdAt) {
    var id = nextId.getAndIncrement();
    var bookmark = new Bookmark(id, request.url(), request.title(), request.tags(), createdAt);
    bookmarks.put(id, bookmark);
    return bookmark;
  }

  public Optional<Bookmark> findById(long id) {
    return Optional.ofNullable(bookmarks.get(id));
  }

  public Optional<Bookmark> findByUrl(String url) {
    return bookmarks.values().stream().filter(bookmark -> bookmark.url().equals(url)).findFirst();
  }

  public List<Bookmark> findAll() {
    return bookmarks.values().stream().sorted(Comparator.comparingLong(Bookmark::id)).toList();
  }

  public boolean delete(long id) {
    return bookmarks.remove(id) != null;
  }
}
