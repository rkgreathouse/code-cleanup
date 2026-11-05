package com.example.bookmarks.errors;

public class ConflictException extends ApiException {

  public ConflictException(String message) {
    super(message);
  }
}
