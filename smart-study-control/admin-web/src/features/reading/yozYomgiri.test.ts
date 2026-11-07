import { describe, expect, it } from "vitest";
import { YOZ_YOMGIRI_PAGES_1_5 } from "./yozYomgiri";

describe("Yoz yomg‘iri starter reading test", () => {
  it("keeps every question inside the assigned five-page range", () => {
    expect(YOZ_YOMGIRI_PAGES_1_5.questions).toHaveLength(10);
    for (const question of YOZ_YOMGIRI_PAGES_1_5.questions) {
      expect(question.source_page).toBeGreaterThanOrEqual(1);
      expect(question.source_page).toBeLessThanOrEqual(5);
      expect(question.source_quote.length).toBeGreaterThanOrEqual(8);
      expect(question.options.length).toBeGreaterThanOrEqual(2);
      expect(question.options.length).toBeLessThanOrEqual(5);
      expect(new Set(question.options).size).toBe(question.options.length);
      expect(question.correct_index).toBeGreaterThanOrEqual(0);
      expect(question.correct_index).toBeLessThan(question.options.length);
    }
  });

  it("keeps the concept source within the selected page range", () => {
    expect(YOZ_YOMGIRI_PAGES_1_5.concepts).toHaveLength(1);
    for (const concept of YOZ_YOMGIRI_PAGES_1_5.concepts) {
      expect(concept.source_page).toBeGreaterThanOrEqual(1);
      expect(concept.source_page).toBeLessThanOrEqual(5);
      expect(concept.source_quote.length).toBeGreaterThanOrEqual(8);
    }
  });
});
