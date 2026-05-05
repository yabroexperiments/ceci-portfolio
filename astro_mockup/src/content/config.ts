// Content collection schema. Astro validates each Markdown file's
// frontmatter against this — Ceci can't accidentally save a broken page
// (e.g. typo'd a layout name; forgot a required field). She gets an error
// in her editor or in the GitHub web UI commit preview.
import { defineCollection, z } from 'astro:content';

const projects = defineCollection({
  type: 'content',
  schema: z.object({
    // What appears as the big headline on the page and in the gallery card
    title: z.string(),
    // Small label above the title (e.g. "BINANCE", "HTC", "MOZILLA")
    subtitle: z.string().optional(),
    // The 1–3 sentence intro paragraph
    description: z.string(),
    // Which layout template to use — type-checked at build time.
    // Named `template` (not `layout`) because `layout` is reserved by Astro
    // for its automatic Markdown-layout import resolution.
    template: z.enum(['hero-composition', 'image-grid', 'profile', 'dark-hero']),
    // For hero-composition: the device mockup images that compose the hero
    hero_images: z.array(z.string()).optional(),
    // For image-grid: the gallery images, each with optional caption
    images: z.array(
      z.object({
        src: z.string(),
        caption: z.string().optional(),
      })
    ).optional(),
    // Hero / accent background color (any CSS color string)
    background_color: z.string().optional(),
    // Optional grouping for the homepage gallery (e.g. "binance", "htc")
    category: z.string().optional(),
    // Optional ordering — lower numbers appear first within a category
    order: z.number().optional(),
    // Whether to show on the homepage gallery (default true)
    featured: z.boolean().optional().default(true),
  }),
});

export const collections = { projects };
