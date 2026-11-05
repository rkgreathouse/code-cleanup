package com.example.bookmarks;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

@SpringBootTest
class ApplicationTest {

  @Autowired private Settings settings;

  @Test
  void loadsSettingsFromApplicationYml() {
    assertThat(settings).isEqualTo(new Settings(20, 10));
  }
}
