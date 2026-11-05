package com.example.bookmarks.errors;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;

class ErrorHandlerTest {

  private final ErrorHandler handler = new ErrorHandler();

  @Test
  void answersEachFailureWithItsStatusAndMessage() {
    var notFound = handler.handleNotFound(new NotFoundException("no bookmark 7"));
    var conflict = handler.handleConflict(new ConflictException("already bookmarked"));
    var invalid = handler.handleInvalidRequest(new InvalidRequestException("too many tags"));

    assertThat(notFound.getStatus()).isEqualTo(HttpStatus.NOT_FOUND.value());
    assertThat(conflict.getStatus()).isEqualTo(HttpStatus.CONFLICT.value());
    assertThat(invalid.getStatus()).isEqualTo(HttpStatus.BAD_REQUEST.value());
    assertThat(invalid).extracting(ProblemDetail::getDetail).isEqualTo("too many tags");
  }
}
