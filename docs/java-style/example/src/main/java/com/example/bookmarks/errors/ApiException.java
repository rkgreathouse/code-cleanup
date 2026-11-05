package com.example.bookmarks.errors;

public abstract class ApiException extends RuntimeException {

  protected ApiException(String message) {
    super(message);
  }
}
