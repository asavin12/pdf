import os
import base64
import re

# Đường dẫn tới thư mục images và tệp CSS
images_dir = "images"  # Thư mục chứa các tệp .png
css_input_file = "viewer.css"  # Tệp CSS gốc
css_output_file = "viewer_modified.css"  # Tệp CSS sau khi chỉnh sửa

# Hàm chuyển đổi tệp PNG thành Data URL
def png_to_data_url(png_path):
    with open(png_path, "rb") as f:
        png_content = f.read()
        base64_encoded = base64.b64encode(png_content).decode("utf-8")
        return f"data:image/png;base64,{base64_encoded}"

# Hàm lấy danh sách tệp PNG và tạo từ điển ánh xạ tên tệp gốc (.svg) -> Data URL (.png)
def get_png_data_urls(directory):
    png_data_urls = {}
    for filename in os.listdir(directory):
        if filename.endswith(".png"):
            svg_filename = filename.replace(".png", ".svg")
            png_path = os.path.join(directory, filename)
            png_data_urls[svg_filename] = png_to_data_url(png_path)
    return png_data_urls

# Hàm thay thế url trong :root và sửa mask-image thành background-image
def replace_urls_and_masks_in_css(css_content, png_data_urls):
    # 1. Thay thế các url trong :root
    pattern_url = r'url\((images/[^"\s)]+\.svg)\)'
    
    def replace_url_match(match):
        svg_filename = match.group(1).replace("images/", "")
        if svg_filename in png_data_urls:
            return f'url({png_data_urls[svg_filename]})'
        return match.group(0)
    
    modified_css = re.sub(pattern_url, replace_url_match, css_content)

    # 2. Thay thế mask-image thành background-image trong các khối ::before
    pattern_mask = r'(-webkit-mask-image|mask-image):\s*var\((--toolbarButton-[^)]+-icon)\);'
    
    def replace_mask_match(match):
        prop, var_name = match.groups()
        # Lấy Data URL từ biến đã thay thế trong :root
        var_pattern = rf'{var_name}:\s*url\((data:image/png;base64,[^)]+)\);'
        var_match = re.search(var_pattern, modified_css)
        if var_match:
            data_url = var_match.group(1)
            return (
                f"background-image: url({data_url});\n"
                "  background-size: 16px 16px;\n"
                "  background-repeat: no-repeat;\n"
                "  background-position: center;"
            )
        return match.group(0)

    modified_css = re.sub(pattern_mask, replace_mask_match, modified_css)

    # 3. Xóa background-color không cần thiết trong các nút
    modified_css = re.sub(
        r'(\.toolbarButton\s*::before[^}]*?)background-color:\s*var\(--toolbar-icon-bg-color\);',
        r'\1',
        modified_css,
        flags=re.DOTALL
    )

    # 4. Xóa mask-size không cần thiết
    modified_css = re.sub(r'(-webkit-mask-size|mask-size):\s*cover;', '', modified_css)

    return modified_css

# Thực thi chương trình
def main():
    if not os.path.exists(images_dir):
        print(f"Thư mục '{images_dir}' không tồn tại!")
        return
    if not os.path.exists(css_input_file):
        print(f"Tệp '{css_input_file}' không tồn tại!")
        return

    png_data_urls = get_png_data_urls(images_dir)
    print(f"Đã tìm thấy {len(png_data_urls)} tệp PNG trong thư mục '{images_dir}'.")

    with open(css_input_file, "r", encoding="utf-8") as f:
        css_content = f.read()

    modified_css = replace_urls_and_masks_in_css(css_content, png_data_urls)

    with open(css_output_file, "w", encoding="utf-8") as f:
        f.write(modified_css)
    
    print(f"Đã tạo tệp CSS mới: '{css_output_file}' với các biểu tượng PNG được nhúng.")

if __name__ == "__main__":
    main()
