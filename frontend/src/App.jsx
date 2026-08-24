// App.jsx
import { RouterProvider } from "react-router-dom";
import { router } from "./router";
import { ThemeProvider } from "./store/ThemeProvider";
import "./styles/global.css";
import "./assets/fonts/icomoon/style.css";

const App = () => {
  return (
    <ThemeProvider>
      <RouterProvider router={router} />
    </ThemeProvider>
  );
};

export default App;
