export const isAuthenticated = () => {
  return !!localStorage.getItem("token");
};

export const setUserInfo = (token, user) => {
  localStorage.setItem("token", token);
  if (user) {
    if (user.username) localStorage.setItem("username", user.username);
    if (user.id) localStorage.setItem("userId", user.id);
    if (user.avatar) localStorage.setItem("avatar", user.avatar);
  }
};

export const getCurrentUser = () => {
  return {
    token: localStorage.getItem("token"),
    username: localStorage.getItem("username") || "",
    id: localStorage.getItem("userId") || "",
    avatar: localStorage.getItem("avatar") || "",
  };
};

export const logout = () => {
  localStorage.removeItem("token");
  localStorage.removeItem("username");
  localStorage.removeItem("userId");
  localStorage.removeItem("avatar");
};
