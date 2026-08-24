// hooks/usePageTransition.js
import { useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";

export const usePageTransition = () => {
  const [isTransitioning, setIsTransitioning] = useState(false);
  const navigate = useNavigate();

  const navigateWithLoading = useCallback(
    (path, delay = 5000) => {
      // 显示 Loading
      setIsTransitioning(true);

      // 延迟后执行跳转
      setTimeout(() => {
        navigate(path);
        // 跳转后延迟隐藏 Loading（确保新页面加载完成）
        setTimeout(() => {
          setIsTransitioning(false);
        }, 500);
      }, delay);
    },
    [navigate],
  );

  const handleLoadingComplete = useCallback(() => {
    // Loading 动画完成后的回调
    console.log("Loading completed");
  }, []);

  return {
    isTransitioning,
    navigateWithLoading,
    handleLoadingComplete,
  };
};
