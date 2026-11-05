package com.example.bookmarks;

import jakarta.validation.constraints.Positive;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.validation.annotation.Validated;

@Validated
@ConfigurationProperties("bookmarks")
public record Settings(@Positive int pageSize, @Positive int maxTags) {}
