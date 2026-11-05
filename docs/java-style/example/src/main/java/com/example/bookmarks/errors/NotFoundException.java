package com.example.bookmarks.errors;

public class NotFoundException extends ApiException {

  public NotFoundException(String message) {
    super(message);
  }
}
