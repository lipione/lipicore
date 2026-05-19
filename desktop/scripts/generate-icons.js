const fs = require("node:fs");
const path = require("node:path");
const png2icons = require("png2icons");
const sharp = require("sharp");

const root = path.resolve(__dirname, "..");
const assetDir = path.join(root, "assets");
const svgPath = path.join(assetDir, "logo.svg");
const pngPath = path.join(assetDir, "icon-1024.png");
const icnsPath = path.join(assetDir, "icon.icns");
const icoPath = path.join(assetDir, "icon.ico");

async function main() {
  await sharp(svgPath)
    .resize(1024, 1024)
    .png()
    .toFile(pngPath);

  const pngBuffer = fs.readFileSync(pngPath);
  const icnsBuffer = png2icons.createICNS(pngBuffer, png2icons.BILINEAR, 0);
  const icoBuffer = png2icons.createICO(pngBuffer, png2icons.BILINEAR, 0);

  if (!icnsBuffer || !icoBuffer) {
    throw new Error("Icon generation failed");
  }

  fs.writeFileSync(icnsPath, icnsBuffer);
  fs.writeFileSync(icoPath, icoBuffer);
  fs.rmSync(pngPath, { force: true });

  console.log("Generated desktop/assets/icon.icns and desktop/assets/icon.ico");
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
