import { createBrowserRouter, Outlet } from "react-router-dom";
import { lazy } from "react";
import { withSuspenseRoutes } from "../utils/withSuspenseRoutes";
import Loading from "../components/Loading/Loading";
import RequireAuth from "../components/RequireAuth/RequireAuth";

const MainLayout = lazy(() => import("../layouts/MainLayout/MainLayout"));
const Home = lazy(() => import("../pages/Home/Home"));
const Detect = lazy(() => import("../pages/Detect/Detect"));
const Analysis = lazy(() => import("../pages/Analysis/Analysis"));
const Reports = lazy(() => import("../pages/Reports/Reports"));
const Knowledge = lazy(() => import("../pages/Knowledge/Knowledge"));
const User = lazy(() => import("../pages/User/User"));
const NotFound = lazy(() => import("../pages/NotFound/NotFound"));
const LogoPoint = lazy(() => import("../components/LogoPoint/LogoPoint"));
const Login = lazy(() => import("../pages/Login/Login"));
const ArticleDetail = lazy(() => import("../pages/Knowledge/ArticleDetail"));
const CaseDetail = lazy(() => import("../pages/Knowledge/CaseDetail"));

const protectedPage = (page) => <RequireAuth>{page}</RequireAuth>;

const routeConfig = [
  {
    path: "/",
    element: <MainLayout />,
    children: [
      { index: true, element: <Home /> },
      { path: "detect", element: protectedPage(<Detect />) },
      { path: "analysis", element: protectedPage(<Analysis />) },
      { path: "reports", element: protectedPage(<Reports />) },
      {
        path: "knowledge",
        element: protectedPage(<Outlet />),
        children: [
          { index: true, element: <Knowledge /> },
          { path: "article/:id", element: <ArticleDetail /> },
          { path: "case/:id", element: <CaseDetail /> },
        ],
      },
      { path: "user", element: protectedPage(<User />) },
    ],
  },
  { path: "/login", element: <Login /> },
  { path: "/logo", element: <LogoPoint /> },
  { path: "*", element: <NotFound /> },
];

const enhancedRoutes = withSuspenseRoutes(routeConfig, <Loading />);

export const router = createBrowserRouter(enhancedRoutes, { basename: "/" });
export const routes = routeConfig;
