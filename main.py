import os
import shutil
import subprocess
from PIL import Image, ImageDraw, ImageFont
import textwrap


def generate_video(output_video, background_music, texts, audio_names, image_names):
    """
    生成视频
    :param output_video: 视频生成的路径
    :param background_music: 最终视频生成的背景音乐，注意，背景音乐是时常通常要比视频时长要长
    :param texts: 要生成的文字列表
    :param audio_names: 文字对应的音频对应的文件名列表 跟文字列表一一对应
    :param image_names: 文字对应的图片列表 跟文字列表一一对应
    :return:
    """
    current_file = __file__  # 当前文件的路径
    current_dir = os.path.abspath(os.path.dirname(current_file))  # 当前文件所在的目录

    # 创建临时文件夹用于存储生成的中间文件
    temp_dir = 'temp'
    os.makedirs(temp_dir, exist_ok=True)
    # 生成每张图片的视频片段
    video_clips = []

    # 遍历文本，生成图片和音频片段
    for i, text in enumerate(texts):
        # 随机获取一张使用爬虫爬下来的图片作为背景图
        image_path = os.path.join(f'{current_dir}\\images', image_names[i])
        # 背景图上面要加的音频路径，与文本一一对应
        audio_path = os.path.join('audios', f'{audio_names[i]}')
        # 每个图片和音频生成的视频片段保存位置
        video_clip_path = os.path.join(temp_dir, f'video_{i}.mp4')

        # 添加文字到图片
        # 打开图片
        image = Image.open(image_path)
        # 获取图片宽度
        image_width = image.width
        font_size = 80  # 假设文字大小为80像素
        # 设置字体
        font_file = 'simhei.ttf'  # 字体文件路径
        font = ImageFont.truetype(font_file, font_size)

        # 创建一个绘图对象
        draw = ImageDraw.Draw(image)
        # 获取文字的宽度(获取指定字体一个文字的宽度)
        text_width, _ = draw.textsize("好", font=font)

        # 根据图片宽度，文字宽度计算每行显示多少个文字，超过自动换行
        chars_per_line = int(image_width / text_width)  # 根据实际情况调整字符宽度比例

        # 获取底层颜色 根据亮度显示不同的文字颜色
        background_color = image.getpixel((0, 0))

        # 计算底层颜色的亮度值
        brightness = sum(background_color) / 3

        # 根据亮度值选择文字颜色
        if brightness < 128:
            color = 'white'
        else:
            color = 'black'

        # 使用textwrap模块将一行文本拆分为多行
        lines = textwrap.wrap(text, width=chars_per_line)
        my_text = str.join("\n\n", lines)

        # 配上文字之后的图片存放的临时路径
        text_image_path = os.path.join(temp_dir, f'text_image_{i}.jpg')

        # 绘图 图片+文字
        subprocess.run(['ffmpeg', '-i', image_path, '-vf',
                        f"drawtext=text='{my_text}':x=(w-text_w)/2:y=(h-text_h)/2:fontsize={font_size}:fontcolor={color}:fontfile={font_file}",
                        text_image_path])
        print(f'给图片【{image_path}】添加文字【{my_text}】成功')

        # 获取音频时长 根据音频长度决定视频片段显示的时长
        duration = int(float(subprocess.check_output(
            ['ffprobe', '-i', audio_path, '-show_entries', 'format=duration', '-v', 'quiet', '-of', 'csv=p=0'])))

        print(f'获取音频【{audio_path}】长度成功，时长：{duration}s')

        if not os.path.exists(audio_path):
            print(audio_path + '不存在')
            continue

        # 循环生成视频片段 1920:1080表示分辨率
        subprocess.run(['ffmpeg', '-loop', '1', '-i', text_image_path, '-i', audio_path, '-c:v', 'libx264', '-t',
                        f'{duration+1}', '-pix_fmt', 'yuv420p', '-vf', 'scale=1920:1080', '-c:a', 'aac', '-strict', '-2',
                        '-shortest', video_clip_path])

        print(f'生成视频片段【{video_clip_path}】成功')

        # 将生成的视频片段的路径存起来
        video_clips.append(video_clip_path)

    # 拼接生成好的视频片段路径写入一个临时文件中
    video_list_file = os.path.join(temp_dir, 'video_list.txt')
    with open(video_list_file, 'w') as f:
        for clip in video_clips:
            clip = current_dir + '\\' + clip
            f.write(f"file '{clip}'\n")

    # 拼接多个视频片段成为一个（视频合成/链接）
    concat_output = os.path.join(temp_dir, 'concatenated_video.mp4')
    subprocess.run(['ffmpeg', '-f', 'concat', '-safe', '0', '-i', video_list_file, '-c', 'copy', '-y', concat_output])
    print(f'合成视频片段{video_list_file}为【{concat_output}】成功')

    if os.path.exists(output_video):
        os.remove(output_video)

    # 使用FFmpeg将视频和音频混流，从而在不影响音频的情况下添加背景音乐
    subprocess.run(['ffmpeg', '-i', current_dir + '\\' + concat_output, '-i', background_music, '-filter_complex',
                    '[0:a][1:a]amix=inputs=2:duration=shortest', '-c:v', 'copy', '-c:a', 'aac', output_video])

    print(f'合成视频片段【{concat_output}】后添加背景音乐【{background_music}】成功')

    # 删除临时文件
    shutil.rmtree(temp_dir)
    if os.path.exists(current_dir + '\\' + concat_output):
        os.remove(current_dir + '\\' + concat_output)
    print('生成视频结束，并已删除产生的临时文件')


if __name__ == '__main__':
    texts = ['我手上划了一道口子你也划一条吧 这样咱俩就是两口子了', '我是九，你是三，除了你还是你。']
    audio_names = ['1.wav', '2.wav']

    # 设置输出视频路径
    output_video = 'my_video.mp4'

    # 背景音乐路径
    background_music = 'back_music\\music.mp3'

    # 图片路径
    image_names = ['1.jpg', '2.jpg']

    # 设置图片和配音文件目录
    generate_video(output_video, background_music, texts, audio_names, image_names)
