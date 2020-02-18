# -*- coding: utf-8 -*-
from PIL import Image
import StringIO
from django.conf import settings
from django.core.files.base import ContentFile
import tinify
from vk.logs import log


IMAGE_BACKGROUND_COLOR = "#1a1a1a"
tinify.key = settings.TINYPNG_API_KEY


def remove_transparency(im, bg_color=(0xdd, 0xdd, 0xdd)):
    # Only process if image has transparency (http://stackoverflow.com/a/1963146)
    if im.mode in ('RGBA', 'LA') or (im.mode == 'P' and 'transparency' in im.info):
        # Need to convert to RGBA if LA format due to a bug in PIL (http://stackoverflow.com/a/1963146)
        alpha = im.convert('RGBA').split()[-1]
        # Create a new background image of our matt color.
        # Must be RGBA because paste requires both images have the same format
        # (http://stackoverflow.com/a/8720632  and  http://stackoverflow.com/a/9459208)
        bg = Image.new("RGBA", im.size, bg_color + (255,))
        bg.paste(im, mask=alpha)
        return bg
    else:
        return im


def convert_for_product(product, old):
    # has original
    if not product.image_original:
        product.image_compressed = None
        return
    # make sure image has been changed
    if product.image_original == old.image_original and old.image_compressed_with_tinypng:
        return

    img = Image.open(product.image_original)
    bg_color = int(IMAGE_BACKGROUND_COLOR[1:3], base=16), int(IMAGE_BACKGROUND_COLOR[3:5], base=16), int(IMAGE_BACKGROUND_COLOR[5:7], base=16)
    img = remove_transparency(img, bg_color=bg_color)

    try:
        img_io = StringIO.StringIO()
        img.save(img_io, format='PNG')
        source = tinify.from_buffer(img_io.getvalue())
        data = source.to_buffer()
        img_content = ContentFile(data, product.image_original.name)
        product.image_compressed = img_content
        product.image_compressed_with_tinypng = True
    except tinify.Error:
        log.exception("Unable to use TinyPNG for image, fallback to server's algorithm")
        # This gives much more coarse results then TinyPNG
        # See API https://tinypng.com/developers/reference/python
        img_8bit = img.convert(
            mode='P',
            palette=Image.ADAPTIVE,
            colors=256,
        )
        img_io = StringIO.StringIO()
        img_8bit.save(
            img_io,
            format='PNG',
            optimize=True,
        )
        img_content = ContentFile(img_io.getvalue(), product.image_original.name)
        product.image_compressed = img_content
        product.image_compressed_with_tinypng = False

