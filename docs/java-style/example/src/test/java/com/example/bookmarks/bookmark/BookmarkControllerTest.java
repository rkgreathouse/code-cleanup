package com.example.bookmarks.bookmark;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.test.annotation.DirtiesContext;
import org.springframework.test.web.servlet.assertj.MockMvcTester;

@SpringBootTest
@AutoConfigureMockMvc
@DirtiesContext(classMode = DirtiesContext.ClassMode.AFTER_EACH_TEST_METHOD)
class BookmarkControllerTest {

  @Autowired private MockMvcTester mvc;

  @Test
  void createsABookmarkAndReadsItBack() {
    var created = post("{\"url\": \"https://a.example\", \"title\": \"A\", \"tags\": [\"java\"]}");

    assertThat(created).hasStatus(HttpStatus.CREATED);
    assertThat(mvc.get().uri("/bookmarks/1"))
        .hasStatusOk()
        .bodyJson()
        .extractingPath("$.title")
        .isEqualTo("A");
  }

  @Test
  void answersAnInvalidBodyWithBadRequest() {
    assertThat(post("{\"url\": \"not a url\", \"title\": \"\", \"tags\": []}"))
        .hasStatus(HttpStatus.BAD_REQUEST);
  }

  @Test
  void answersAMissingBookmarkWithAProblemDetail() {
    assertThat(mvc.get().uri("/bookmarks/7"))
        .hasStatus(HttpStatus.NOT_FOUND)
        .bodyJson()
        .extractingPath("$.detail")
        .isEqualTo("no bookmark 7");
  }

  @Test
  void deletesABookmark() {
    var created = post("{\"url\": \"https://a.example\", \"title\": \"A\", \"tags\": []}");

    assertThat(created).hasStatus(HttpStatus.CREATED);
    assertThat(mvc.delete().uri("/bookmarks/1")).hasStatus(HttpStatus.NO_CONTENT);
    assertThat(mvc.get().uri("/bookmarks/1")).hasStatus(HttpStatus.NOT_FOUND);
  }

  private MockMvcTester.MockMvcRequestBuilder post(String body) {
    return mvc.post().uri("/bookmarks").contentType(MediaType.APPLICATION_JSON).content(body);
  }
}
