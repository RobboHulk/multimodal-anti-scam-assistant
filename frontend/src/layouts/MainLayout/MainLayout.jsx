import { Outlet } from "react-router-dom";

const MainLayout = () => {
  return (
    <div className="app">
      <Outlet />
    </div>
  );
};

export default MainLayout;
