from PIL import Image, ImageDraw
import os

def create_icon():
    # Create icon in multiple sizes for better quality
    sizes = [16, 32, 48, 64, 128, 256]
    images = []
    
    for size in sizes:
        # Create image with transparent background
        image = Image.new('RGBA', (size, size), color=(0, 0, 0, 0))
        dc = ImageDraw.Draw(image)
        
        # Calculate circle dimensions
        padding = size // 8
        circle_size = size - (padding * 2)
        
        # Draw circle
        dc.ellipse(
            [padding, padding, size-padding, size-padding],
            fill='white'
        )
        
        images.append(image)
    
    # Save as ICO file
    images[0].save(
        'icon.ico',
        format='ICO',
        sizes=[(size, size) for size in sizes],
        append_images=images[1:]
    )
    
    print("Icon file 'icon.ico' has been created successfully!")

if __name__ == "__main__":
    create_icon() 