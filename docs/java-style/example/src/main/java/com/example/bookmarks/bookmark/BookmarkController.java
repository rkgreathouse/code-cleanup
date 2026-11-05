package com.example.bookmarks.bookmark;

import jakarta.validation.Valid;
import java.util.List;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/bookmarks")
public class BookmarkController {

  private final BookmarkService service;

  public BookmarkController(BookmarkService service) {
    this.service = service;
  }

  @PostMapping
  @ResponseStatus(HttpStatus.CREATED)
  public Bookmark addBookmark(@Valid @RequestBody BookmarkRequest request) {
    return service.addBookmark(request);
  }

  @GetMapping("/{id}")
  public Bookmark getBookmark(@PathVariable long id) {
    return service.findBookmark(id);
  }

  @GetMapping
  public List<Bookmark> listBookmarks(
      @RequestParam(required = false) String tag, @RequestParam(defaultValue = "0") int page) {
    return service.listBookmarks(tag, page);
  }

  @DeleteMapping("/{id}")
  @ResponseStatus(HttpStatus.NO_CONTENT)
  public void removeBookmark(@PathVariable long id) {
    service.removeBookmark(id);
  }
}
