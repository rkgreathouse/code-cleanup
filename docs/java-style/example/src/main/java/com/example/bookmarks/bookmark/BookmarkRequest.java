package com.example.bookmarks.bookmark;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import java.util.Set;
import org.hibernate.validator.constraints.URL;

public record BookmarkRequest(
    @NotBlank @URL String url, @NotBlank String title, @NotNull Set<String> tags) {}
