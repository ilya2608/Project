import { AppBar, Box, Button, Toolbar, Typography } from "@mui/material";
import { Link as RouterLink, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export function NavBar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  return (
    <AppBar position="static" color="default" elevation={1}>
      <Toolbar sx={{ gap: 2 }}>
        <Typography variant="h6" component={RouterLink} to="/" sx={{ textDecoration: "none", color: "inherit", flexGrow: 1 }}>
          Doctor Booking
        </Typography>

        {user?.role === "patient" && (
          <>
            <Button component={RouterLink} to="/patient/doctors">Find a doctor</Button>
            <Button component={RouterLink} to="/patient/appointments">My appointments</Button>
          </>
        )}
        {user?.role === "doctor" && (
          <>
            <Button component={RouterLink} to="/doctor/agenda">Agenda</Button>
            <Button component={RouterLink} to="/doctor/availability">Availability</Button>
          </>
        )}
        {user?.role === "admin" && (
          <>
            <Button component={RouterLink} to="/admin/doctors">Doctors</Button>
            <Button component={RouterLink} to="/admin/appointments">All appointments</Button>
          </>
        )}

        {user ? (
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <Typography variant="body2">{user.full_name}</Typography>
            <Button onClick={handleLogout}>Log out</Button>
          </Box>
        ) : (
          <Button component={RouterLink} to="/login">Log in</Button>
        )}
      </Toolbar>
    </AppBar>
  );
}
