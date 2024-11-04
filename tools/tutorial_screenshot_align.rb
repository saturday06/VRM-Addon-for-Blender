#!/usr/bin/env ruby
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
# frozen_string_literal: true

require "fileutils"
require "pathname"
require "rmagick"

input_path = ARGV[0]
raise "No input path" unless input_path

image = Magick::ImageList.new(input_path).first
base_columns = 660
if image.columns % base_columns > 0
  raise "Image width is not a multiple of #{base_columns} pixels but #{image.columns}"
end
pixels = image.get_pixels(0, 0, image.columns, image.rows)

crop_top = 0
crop_bottom = 0

(0...image.rows).each do |row|
  break unless (0...image.columns).all? { |column| pixels[image.columns * row + column].alpha < 0.0001 }
  crop_top = row + 1
end

(0...image.rows).to_a.reverse.each.with_index do |row, i|
  break unless (0...image.columns).all? { |column| pixels[image.columns * row + column].alpha < 0.0001 }
  crop_bottom = i + 1
end

before_crop_columns = image.columns
before_crop_rows = image.rows - crop_top - crop_bottom
image.crop!(0, crop_top, before_crop_columns + 1, before_crop_rows)
if image.columns != before_crop_columns
  raise "After crop! image width is not #{before_crop_columns} pixels but #{image.columns}"
end
if image.rows != before_crop_rows
  raise "After crop! image height is not #{before_crop_rows} pixels but #{image.rows}"
end

rows = image.rows
while rows % 12 != 0 do
  rows += 1
end
crop_pad_image = Magick::Image.new(image.columns, rows).matte_floodfill(1, 1)
crop_pad_image.composite!(image, Magick::NorthGravity, Magick::OverCompositeOp)

# avif
# crop_pad_image.write(Pathname(input_path).sub_ext(".avif")) do |options|
#   options.quality = 80
#   options.define("heic", "speed", 0)
# end

# png
zopflipng_input_path = input_path + ".tmp.png"
crop_pad_image.write(zopflipng_input_path)
system("zopflipng", "-my", zopflipng_input_path, input_path) or fail
FileUtils.rm(zopflipng_input_path)
