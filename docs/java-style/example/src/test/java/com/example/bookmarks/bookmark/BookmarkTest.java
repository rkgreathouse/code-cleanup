package com.example.bookmarks.bookmark;

import static org.assertj.core.api.Assertions.assertThat;

import java.time.Instant;
import java.util.Set;
import org.junit.jupiter.api.Test;

class BookmarkTest {

  @Test
  void hasOnlyItsOwnTags() {
    var bookmark = new Bookmark(1, "https://a.example", "A", Set.of("java"), Instant.EPOCH);

    assertThat(bookmark.hasTag("java")).isTrue();
    assertThat(bookmark.hasTag("python")).isFalse();
  }
}
