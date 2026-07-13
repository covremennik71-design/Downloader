import struct
import os
import sys

def create_ico(filepath, size=32):
    """
    Creates a valid ICO file with a gradient icon.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    # ICO Header (6 bytes)
    # Reserved: 0, Type: 1 (icon), Count: 1 (one image)
    ico_header = struct.pack('<HHH', 0, 1, 1)
    
    # Image data - create a nice gradient icon
    width = size
    height = size
    
    # BMP Info Header (40 bytes)
    # Height is doubled for ICO format (includes AND mask)
    bmp_header_size = 40
    bmp_header = struct.pack('<IiiHHIIiiII',
        bmp_header_size,  # biSize
        width,            # biWidth
        height * 2,       # biHeight (doubled for ICO)
        1,                # biPlanes
        32,               # biBitCount (32-bit BGRA)
        0,                # biCompression (BI_RGB)
        0,                # biSizeImage
        0, 0,             # biXPelsPerMeter, biYPelsPerMeter
        0, 0              # biClrUsed, biClrImportant
    )
    
    # Pixel data (32x32 BGRA) - Create a gradient download icon
    pixel_data = b''
    for y in range(height):
        for x in range(width):
            # Create a circular gradient with blue/purple colors
            cx, cy = width / 2, height / 2
            dx, dy = x - cx, y - cy
            dist = (dx*dx + dy*dy) ** 0.5
            max_dist = (cx*cx + cy*cy) ** 0.5
            
            # Gradient from center to edge
            t = dist / max_dist if max_dist > 0 else 0
            
            # Blue to purple gradient
            r = int(59 + (139 - 59) * t)
            g = int(130 + (92 - 130) * t)
            b = int(246 + (246 - 246) * t)
            
            # Draw a download arrow in the center
            arrow_color = False
            # Vertical line of arrow
            if width//2 - 2 <= x <= width//2 + 2 and height//4 <= y <= 3*height//4:
                arrow_color = True
            # Bottom triangle of arrow
            if 3*height//4 - 2 <= y <= 3*height//4 + 4:
                tri_width = (y - (3*height//4 - 2)) * 2
                if abs(x - width//2) <= tri_width:
                    arrow_color = True
            
            if arrow_color:
                r, g, b = 255, 255, 255  # White arrow
                a = 255
            else:
                a = 255 if dist < max_dist * 0.9 else int(255 * (1 - (dist - max_dist * 0.9) / (max_dist * 0.1)))
                a = max(0, min(255, a))
            
            pixel_data += struct.pack('<BBBB', b, g, r, a)
    
    # AND mask (1-bit per pixel, padded to 4 bytes per row)
    # For 32x32: 32 pixels = 4 bytes per row, 32 rows = 128 bytes
    row_bytes = (width + 31) // 32 * 4  # Round up to 4-byte boundary
    and_mask = b'\x00' * (row_bytes * height)
    
    # Calculate sizes
    bytes_in_res = bmp_header_size + len(pixel_data) + len(and_mask)
    image_offset = 6 + 16  # ICO header + 1 directory entry
    
    # ICO Directory Entry (16 bytes)
    ico_dir = struct.pack('<BBBBHHII',
        width if width < 256 else 0,    # Width (0 means 256)
        height if height < 256 else 0,  # Height (0 means 256)
        0,                              # Color count (0 for 32-bit)
        0,                              # Reserved
        1,                              # Color planes
        32,                             # Bits per pixel
        bytes_in_res,                   # Size of image data
        image_offset                    # Offset to image data
    )
    
    # Write the ICO file
    with open(filepath, 'wb') as f:
        f.write(ico_header)
        f.write(ico_dir)
        f.write(bmp_header)
        f.write(pixel_data)
        f.write(and_mask)
    
    print(f"Icon created successfully: {filepath}")
    print(f"Size: {width}x{height}, Format: 32-bit BGRA")

def create_png(filepath, size=512):
    """
    Creates a simple PNG file (minimal valid PNG).
    This is a fallback for systems that need PNG icons.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    # Minimal PNG structure
    # PNG signature
    signature = b'\x89PNG\r\n\x1a\n'
    
    # IHDR chunk
    ihdr_data = struct.pack('>IIBBBBB', size, size, 8, 2, 0, 0, 0)  # 8-bit RGB
    ihdr_crc = 0  # We'll use a placeholder
    ihdr = struct.pack('>I', 13) + b'IHDR' + ihdr_data + struct.pack('>I', ihdr_crc)
    
    # IDAT chunk (minimal compressed data - all black)
    import zlib
    raw_data = b''
    for y in range(size):
        raw_data += b'\x00'  # Filter byte
        raw_data += b'\x3b\x82\xf6' * size  # RGB blue color
    
    compressed = zlib.compress(raw_data)
    idat = struct.pack('>I', len(compressed)) + b'IDAT' + compressed + struct.pack('>I', 0)
    
    # IEND chunk
    iend = struct.pack('>I', 0) + b'IEND' + struct.pack('>I', 0xAE426082)
    
    with open(filepath, 'wb') as f:
        f.write(signature)
        f.write(ihdr)
        f.write(idat)
        f.write(iend)
    
    print(f"PNG created: {filepath}")

if __name__ == '__main__':
    # Create main ICO icon
    create_ico('src-tauri/icons/icon.ico', 32)
    
    # Also create larger versions for different uses
    create_ico('src-tauri/icons/32x32.png.ico', 32)
    create_ico('src-tauri/icons/128x128.png.ico', 128)
    
    print("\nAll icons generated successfully!")
