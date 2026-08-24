// Test.jsx
import { useRef, useEffect, useState } from "react";
import styles from "./LogoPoint.module.css";

import logoImg from "../../assets/images/智能体.svg";

// 画幅
const WIDTH = 600;
const HEIGHT = 600;
//动画时间
const ANIMATE_TIME = 30;
//每帧透明度变化步长
const OPACITY_STEP = 1 / ANIMATE_TIME;
//影响半径
const RADIUS = 40;
//力度
const INTEN = 0.95;

// 粒子类
class Particle {
  constructor(totalX, totalY, time, color) {
    //画幅中任意一处
    this.x = Math.floor(Math.random() * WIDTH);
    this.y = Math.floor(Math.random() * HEIGHT);
    this.totalX = totalX;
    this.totalY = totalY;
    this.time = time;
    this.r = 1.2;
    this.color = [...color];
    this.opacity = 0;
  }

  draw(ctx) {
    //rgba
    ctx.fillStyle = `rgba(${this.color.join(",")})`;
    //圆角矩形
    ctx.fillRect(this.x, this.y, this.r * 2, this.r * 2);
  }

  update(mouseX, mouseY) {
    this.mx = this.totalX - this.x;
    this.my = this.totalY - this.y;
    this.vx = this.mx / this.time;
    this.vy = this.my / this.time;

    if (mouseX !== undefined && mouseY !== undefined) {
      const dx = mouseX - this.x;
      const dy = mouseY - this.y;
      const distance = Math.sqrt(dx * dx + dy * dy);

      if (distance > 0) {
        let disPercent = RADIUS / distance;
        disPercent = disPercent > 7 ? 7 : disPercent;

        const angle = Math.atan2(dy, dx);
        const cos = Math.cos(angle);
        const sin = Math.sin(angle);

        const repX = cos * disPercent * -INTEN;
        const repY = sin * disPercent * -INTEN;

        this.vx += repX;
        this.vy += repY;
      }
    }

    this.x += this.vx;
    this.y += this.vy;

    if (this.opacity < 1) this.opacity += OPACITY_STEP;
  }

  change(x, y, color) {
    this.totalX = x;
    this.totalY = y;
    this.color = [...color];
  }
}

// Logo图片类
class LogoImage {
  constructor(src, name) {
    this.src = src;
    this.name = name;
    this.particleData = [];

    const img = new Image();
    img.crossOrigin = "anonymous";
    img.src = src;

    img.onload = () => {
      console.log(`图片加载成功: ${name}`, src);
      const tmpCanvas = document.createElement("canvas");
      const tmpCtx = tmpCanvas.getContext("2d");
      const imgW = WIDTH;
      const imgH = Math.floor(WIDTH * (img.height / img.width));

      tmpCanvas.width = imgW;
      tmpCanvas.height = imgH;
      tmpCtx?.drawImage(img, 0, 0, imgW, imgH);

      const imgData = tmpCtx?.getImageData(0, 0, imgW, imgH).data;
      tmpCtx?.clearRect(0, 0, WIDTH, HEIGHT);

      if (imgData) {
        for (let y = 0; y < imgH; y += 5) {
          for (let x = 0; x < imgW; x += 5) {
            const index = (x + y * imgW) * 4;
            const r = imgData[index];
            const g = imgData[index + 1];
            const b = imgData[index + 2];
            const a = imgData[index + 3];
            const sum = r + g + b + a;

            if (sum >= 100) {
              const particle = new Particle(x, y, ANIMATE_TIME, [r, g, b, a]);
              this.particleData.push(particle);
            }
          }
        }
        console.log(`生成粒子数 ${name}:`, this.particleData.length);
      }
    };

    img.onerror = (error) => {
      console.error(`图片加载失败: ${name}`, src, error);
    };
  }
}

// 画布类
class ParticleCanvas {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
    this.width = canvas.width;
    this.height = canvas.height;
    this.particleArr = [];

    this.canvas.addEventListener("mousemove", (e) => {
      const rect = this.canvas.getBoundingClientRect();
      this.mouseX = e.clientX - rect.left;
      this.mouseY = e.clientY - rect.top;
    });

    this.canvas.addEventListener("mouseleave", () => {
      this.mouseX = undefined;
      this.mouseY = undefined;
    });
  }

  changeImg(img) {
    if (this.particleArr.length) {
      const newPrtArr = img.particleData;
      const newLen = newPrtArr.length;
      const arr = this.particleArr;
      const oldLen = arr.length;

      for (let idx = 0; idx < newLen; idx++) {
        const { totalX, totalY, color } = newPrtArr[idx];
        if (arr[idx]) {
          arr[idx].change(totalX, totalY, color);
        } else {
          arr[idx] = new Particle(totalX, totalY, ANIMATE_TIME, color);
        }
      }

      if (newLen < oldLen) {
        this.particleArr = arr.slice(0, newLen);
      }

      const tmpArr = this.particleArr;
      let tmpLen = tmpArr.length;

      while (tmpLen) {
        const randomIdx = Math.floor(Math.random() * tmpLen--);
        const randomPrt = tmpArr[randomIdx];
        const { totalX: tx, totalY: ty, color } = randomPrt;

        randomPrt.totalX = tmpArr[tmpLen].totalX;
        randomPrt.totalY = tmpArr[tmpLen].totalY;
        randomPrt.color = tmpArr[tmpLen].color;

        tmpArr[tmpLen].totalX = tx;
        tmpArr[tmpLen].totalY = ty;
        tmpArr[tmpLen].color = color;
      }
    } else {
      this.particleArr = img.particleData.map(
        (item) =>
          new Particle(item.totalX, item.totalY, ANIMATE_TIME, item.color),
      );
    }
  }

  drawCanvas() {
    this.ctx.clearRect(0, 0, this.width, this.height);
    this.particleArr.forEach((particle) => {
      particle.update(this.mouseX, this.mouseY);
      particle.draw(this.ctx);
    });
    requestAnimationFrame(() => this.drawCanvas());
  }
}

// React组件 - 只有一个canvas，自动加载logo
const LogoPoint = () => {
  const canvasRef = useRef(null);
  const [particleCanvas, setParticleCanvas] = useState(null);
  const [logoReady, setLogoReady] = useState(false);
  const logoInstanceRef = useRef(null);

  // 初始化logo实例
  useEffect(() => {
    if (!logoInstanceRef.current) {
      const logoInstance = new LogoImage(logoImg, "logo");
      logoInstanceRef.current = logoInstance;

      // 监听图片加载完成
      const checkLogoReady = setInterval(() => {
        if (
          logoInstanceRef.current &&
          logoInstanceRef.current.particleData.length > 0
        ) {
          setLogoReady(true);
          clearInterval(checkLogoReady);
        }
      }, 100);

      return () => clearInterval(checkLogoReady);
    }
  }, []);

  // 初始化Canvas
  useEffect(() => {
    if (canvasRef.current && !particleCanvas) {
      const pc = new ParticleCanvas(canvasRef.current);
      setParticleCanvas(pc);
      pc.drawCanvas();
    }
  }, [particleCanvas]);

  // 当canvas和logo都准备好后，自动加载logo
  useEffect(() => {
    if (particleCanvas && logoReady && logoInstanceRef.current) {
      particleCanvas.changeImg(logoInstanceRef.current);
    }
  }, [particleCanvas, logoReady]);

  return (
    <div className={styles.container}>
      <div className={styles.canvasWrapper}>
        <canvas
          ref={canvasRef}
          width={WIDTH}
          height={HEIGHT}
          className={styles.canvas}
        />
      </div>
    </div>
  );
};

export default LogoPoint;
