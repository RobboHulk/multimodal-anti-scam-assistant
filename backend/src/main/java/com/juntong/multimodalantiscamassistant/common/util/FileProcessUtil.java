package com.juntong.multimodalantiscamassistant.common.util;

import com.juntong.multimodalantiscamassistant.common.exception.BusinessException;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.multipart.MultipartFile;

import javax.imageio.ImageIO;
import java.awt.*;
import java.awt.image.BufferedImage;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;

@Slf4j
public class FileProcessUtil {

    private static final long MAX_IMAGE_SIZE = 10 * 1024 * 1024L; // 10MB
    private static final long MAX_AUDIO_SIZE = 15 * 1024 * 1024L; // 15MB

    /**
     * 魔数特征片段
     */
    private static final byte[] JPEG_MAGIC = new byte[] { (byte) 0xFF, (byte) 0xD8, (byte) 0xFF };
    private static final byte[] PNG_MAGIC = new byte[] { (byte) 0x89, 0x50, 0x4E, 0x47 };
    private static final byte[] WEBP_MAGIC = new byte[] { 0x52, 0x49, 0x46, 0x46 }; // RIFF
    private static final byte[] MP3_MAGIC_1 = new byte[] { 0x49, 0x44, 0x33 }; // ID3
    private static final byte[] MP3_MAGIC_2 = new byte[] { (byte) 0xFF, (byte) 0xFB }; // ADTS
    private static final byte[] MP3_MAGIC_3 = new byte[] { (byte) 0xFF, (byte) 0xF3 };
    private static final byte[] MP3_MAGIC_4 = new byte[] { (byte) 0xFF, (byte) 0xF2 };
    private static final byte[] AMR_MAGIC = new byte[] { 0x23, 0x21, 0x41, 0x4D, 0x52 }; // #!AMR

    public enum FileType {
        IMAGE, AUDIO, UNKNOWN
    }

    /**
     * 校验魔数并返回文件类型
     */
    public static FileType checkMagicAndType(MultipartFile file, String suffix) throws IOException {
        long size = file.getSize();
        byte[] header = new byte[8];
        try (InputStream is = file.getInputStream()) {
            is.read(header, 0, 8);
        }

        suffix = suffix.toLowerCase();

        // 图像判断
        if (suffix.equals(".jpg") || suffix.equals(".jpeg") || suffix.equals(".png") || suffix.equals(".webp")) {
            if (size > MAX_IMAGE_SIZE) {
                throw new BusinessException(400, "图片大小超过 10MB 限制");
            }
            if (startsWith(header, JPEG_MAGIC) || startsWith(header, PNG_MAGIC) || startsWith(header, WEBP_MAGIC)) {
                return FileType.IMAGE;
            }
        }
        // 音频判断
        else if (suffix.equals(".mp3") || suffix.equals(".wav") || suffix.equals(".amr")) {
            if (size > MAX_AUDIO_SIZE) {
                throw new BusinessException(400, "音频大小超过 15MB 限制");
            }
            if (suffix.equals(".wav") && startsWith(header, WEBP_MAGIC)) { // WAV start with RIFF
                return FileType.AUDIO;
            }
            if (suffix.equals(".mp3") && (startsWith(header, MP3_MAGIC_1) || startsWith(header, MP3_MAGIC_2)
                    || startsWith(header, MP3_MAGIC_3) || startsWith(header, MP3_MAGIC_4))) {
                return FileType.AUDIO;
            }
            if (suffix.equals(".amr") && startsWith(header, AMR_MAGIC)) {
                return FileType.AUDIO;
            }
        }

        throw new BusinessException(400, "文件格式不受支持或伪装后缀 (Magic Number Mismatch)");
    }

    /**
     * 处理图像文件：校验分辨率并在必要时转码为 JPEG
     */
    public static File processImageAndTranscode(MultipartFile file, File dest) throws IOException {
        try (InputStream is = file.getInputStream()) {
            BufferedImage image = ImageIO.read(is);
            if (image == null) {
                throw new BusinessException(400, "无法解析的受损图像流");
            }

            int width = image.getWidth();
            int height = image.getHeight();
            // 限制在 100x100 到 4096x4096 之间
            if (width < 100 || height < 100 || width > 4096 || height > 4096) {
                throw new BusinessException(400, "图片分辨率异常，要求尺寸必须在 100x100 ~ 4096x4096 之间。当前：" + width + "x" + height);
            }

            // 如果已经是以 jpg 结尾（且被正确读取），直接保存原生文件即可提高效率
            if (dest.getName().toLowerCase().endsWith(".jpg")) {
                file.transferTo(dest);
                return dest;
            }

            // 格式转归一化为 JPEG
            // 移除透明通道，否则 PNG 写入 JPEG 会全变黑/粉色
            BufferedImage newImage = new BufferedImage(width, height, BufferedImage.TYPE_INT_RGB);
            Graphics2D g = newImage.createGraphics();
            g.drawImage(image, 0, 0, Color.WHITE, null);
            g.dispose();

            // 强制重命名后缀为 .jpg
            String newPath = dest.getAbsolutePath();
            if (newPath.contains(".")) {
                newPath = newPath.substring(0, newPath.lastIndexOf(".")) + ".jpg";
            }
            File finalDest = new File(newPath);
            ImageIO.write(newImage, "jpg", finalDest);
            return finalDest;
        }
    }

    private static boolean startsWith(byte[] array, byte[] prefix) {
        if (array == null || prefix == null || array.length < prefix.length) {
            return false;
        }
        for (int i = 0; i < prefix.length; i++) {
            if (array[i] != prefix[i]) {
                return false;
            }
        }
        return true;
    }
}
