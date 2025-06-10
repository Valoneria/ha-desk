from PIL import Image, ImageDraw
import os

def create_icon():
    # Create build directory if it doesn't exist
    build_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'build')
    os.makedirs(build_dir, exist_ok=True)
    
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
    
    # Save as ICO file in build directory
    icon_path = os.path.join(build_dir, 'icon.ico')
    images[0].save(
        icon_path,
        format='ICO',
        sizes=[(size, size) for size in sizes],
        append_images=images[1:]
    )
    
    print(f"Icon file has been created successfully at: {icon_path}")

if __name__ == "__main__":
    create_icon() 