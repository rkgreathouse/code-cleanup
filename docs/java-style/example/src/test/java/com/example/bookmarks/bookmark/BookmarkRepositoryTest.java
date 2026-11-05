package com.example.bookmarks.bookmark;

import static org.assertj.core.api.Assertions.assertThat;

import java.time.Instant;
import java.util.List;
import java.util.Set;
import org.junit.jupiter.api.Test;

class BookmarkRepositoryTest {

  private final BookmarkRepository repository = new BookmarkRepository();

  @Test
  void givesEachSavedBookmarkTheNextId() {
    var first = repository.save(request("https://a.example"), Instant.EPOCH);
    var second = repository.save(request("https://b.example"), Instant.EPOCH);

    assertThat(List.of(first.id(), second.id())).containsExactly(1L, 2L);
  }

  @Test
  void findsABookmarkByUrl() {
    var saved = repository.save(request("https://a.example"), Instant.EPOCH);

    assertThat(repository.findByUrl("https://a.example")).contains(saved);
    assertThat(repository.findByUrl("https://b.example")).isEmpty();
  }

  @Test
  void reportsWhetherADeleteRemovedAnything() {
    var saved = repository.save(request("https://a.example"), Instant.EPOCH);

    assertThat(repository.delete(saved.id())).isTrue();
    assertThat(repository.delete(saved.id())).isFalse();
  }

  private static BookmarkRequest request(String url) {
    return new BookmarkRequest(url, "title", Set.of());
  }
}
