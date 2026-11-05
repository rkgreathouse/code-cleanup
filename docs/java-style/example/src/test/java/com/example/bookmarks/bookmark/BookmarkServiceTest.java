package com.example.bookmarks.bookmark;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.example.bookmarks.Settings;
import com.example.bookmarks.errors.ConflictException;
import com.example.bookmarks.errors.InvalidRequestException;
import com.example.bookmarks.errors.NotFoundException;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.Set;
import org.junit.jupiter.api.Test;

class BookmarkServiceTest {

  private final Clock clock = Clock.fixed(Instant.parse("2026-11-05T14:02:11Z"), ZoneOffset.UTC);
  private final BookmarkService service =
      new BookmarkService(new BookmarkRepository(), new Settings(2, 3), clock);

  @Test
  void stampsANewBookmarkWithTheCurrentTime() {
    var bookmark = service.addBookmark(request("https://a.example", "java"));

    assertThat(bookmark.createdAt()).isEqualTo(clock.instant());
  }

  @Test
  void rejectsTheSameUrlTwice() {
    service.addBookmark(request("https://a.example"));

    assertThatThrownBy(() -> service.addBookmark(request("https://a.example")))
        .isInstanceOf(ConflictException.class);
  }

  @Test
  void rejectsMoreTagsThanTheSettingsAllow() {
    var request = request("https://a.example", "a", "b", "c", "d");

    assertThatThrownBy(() -> service.addBookmark(request))
        .isInstanceOf(InvalidRequestException.class);
  }

  @Test
  void listsOnePageOfBookmarksWithTheTag() {
    service.addBookmark(request("https://a.example", "java"));
    service.addBookmark(request("https://b.example"));
    service.addBookmark(request("https://c.example", "java"));
    service.addBookmark(request("https://d.example", "java"));

    var page = service.listBookmarks("java", 0);

    assertThat(page)
        .extracting(Bookmark::url)
        .containsExactly("https://a.example", "https://c.example");
    assertThat(service.listBookmarks("java", 2)).isEmpty();
  }

  @Test
  void reportsAMissingBookmark() {
    assertThatThrownBy(() -> service.findBookmark(7)).isInstanceOf(NotFoundException.class);
    assertThatThrownBy(() -> service.removeBookmark(7)).isInstanceOf(NotFoundException.class);
  }

  private static BookmarkRequest request(String url, String... tags) {
    return new BookmarkRequest(url, "title", Set.of(tags));
  }
}
