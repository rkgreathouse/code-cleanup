package com.example.bookmarks.bookmark;

import java.time.Instant;
import java.util.Set;

public record Bookmark(long id, String url, String title, Set<String> tags, Instant createdAt) {

  public boolean hasTag(String tag) {
    return tags.contains(tag);
  }
}
