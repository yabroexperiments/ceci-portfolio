// Content collection schema. Astro validates each Markdown/MDX file's
// frontmatter against this — Ceci can't accidentally save a broken page.
import { defineCollection, z } from 'astro:content';

const projects = defineCollection({
  // `content` collection (supports both .md and .mdx now that the MDX
  // integration is installed in astro.config.mjs).
  type: 'content',
  schema: z.object({
    title: z.string(),
    subtitle: z.string().optional(),
    description: z.string(),
    // Optional colored hero with composed mockup images. Skip this for
    // text-first or image-grid case studies — the body MDX will do its own
    // intro.
    hero_images: z.array(z.string()).optional(),
    background_color: z.string().optional(),
    // Homepage gallery metadata
    category: z.string().optional(),
    order: z.number().optional(),
    featured: z.boolean().optional().default(true),
    // Hero thumbnail used on the homepage gallery card. If omitted, falls
    // back to the first hero_image.
    thumbnail: z.string().optional(),
  }),
});

export const collections = { projects };
