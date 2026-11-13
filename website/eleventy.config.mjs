import { eleventyImageTransformPlugin } from "@11ty/eleventy-img";
import { RenderPlugin } from "@11ty/eleventy";
import fs from "fs";
import path from "path";
import postcss from "postcss";
import tailwindcss from "@tailwindcss/postcss";
import MarkdownIt from "markdown-it";

export default function (eleventyConfig) {
  const md = new MarkdownIt({
    html: true,
    linkify: true,
  });

  eleventyConfig.on("eleventy.before", async () => {
    const tailwindInputPath = path.resolve("./styles/app.css");
    const tailwindOutputPath = "./_site/styles/app.css";
    const cssContent = fs.readFileSync(tailwindInputPath, "utf8");
    const outputDir = path.dirname(tailwindOutputPath);

    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }

    const result = await postcss([tailwindcss()]).process(cssContent, {
      from: tailwindInputPath,
      to: tailwindOutputPath,
    });

    fs.writeFileSync(tailwindOutputPath, result.css);
  });

  eleventyConfig.addPassthroughCopy("assets/");
  eleventyConfig.addPassthroughCopy("scripts/");
  eleventyConfig.addPassthroughCopy("styles/");

  // Image plugin
  eleventyConfig.addPlugin(eleventyImageTransformPlugin, {
    formats: ["webp", "jpeg", "png", "svg"],
    urlPath: "img/",
    svgShortCircuit: true,
    defaultAttributes: {
      loading: "lazy",
      decoding: "async",
    },
  });
  eleventyConfig.addPlugin(RenderPlugin);

  eleventyConfig.addPairedShortcode("markdown", (content) => {
    return md.render(content);
  });

  return {
    dir: {
      data: "_data",
      includes: "_includes",
      layouts: "_layouts",
    },
  };
}
