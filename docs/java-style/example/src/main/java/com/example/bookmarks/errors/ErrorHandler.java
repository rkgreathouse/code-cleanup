package com.example.bookmarks.errors;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class ErrorHandler {

  private static final Logger log = LoggerFactory.getLogger(ErrorHandler.class);

  @ExceptionHandler(NotFoundException.class)
  public ProblemDetail handleNotFound(NotFoundException error) {
    return toProblem(HttpStatus.NOT_FOUND, error);
  }

  @ExceptionHandler(ConflictException.class)
  public ProblemDetail handleConflict(ConflictException error) {
    return toProblem(HttpStatus.CONFLICT, error);
  }

  @ExceptionHandler(InvalidRequestException.class)
  public ProblemDetail handleInvalidRequest(InvalidRequestException error) {
    return toProblem(HttpStatus.BAD_REQUEST, error);
  }

  private ProblemDetail toProblem(HttpStatus status, ApiException error) {
    log.warn("{}: {}", status, error.getMessage());
    return ProblemDetail.forStatusAndDetail(status, error.getMessage());
  }
}
