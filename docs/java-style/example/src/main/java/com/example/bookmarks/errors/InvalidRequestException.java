package com.example.bookmarks.errors;

public class InvalidRequestException extends ApiException {

  public InvalidRequestException(String message) {
    super(message);
  }
}
