import { Box, Button, Container, Link, Paper, Typography } from "@mui/material";
import { Link as RouterLink } from "react-router-dom";
import { itsmeLoginUrl } from "../api/client";

export function LoginPage() {
  return (
    <Container maxWidth="sm" sx={{ mt: 8 }}>
      <Paper sx={{ p: 4, textAlign: "center" }}>
        <Typography variant="h5" gutterBottom>
          Log in to book an appointment
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Patients log in securely with itsme — no password to remember.
        </Typography>
        <Box>
          <Button
            variant="contained"
            size="large"
            color="warning"
            href={itsmeLoginUrl()}
            sx={{ minWidth: 240 }}
          >
            Log in with itsme
          </Button>
        </Box>
        <Typography variant="body2" sx={{ mt: 4 }}>
          Doctor or staff member? <Link component={RouterLink} to="/staff-login">Log in here</Link>
        </Typography>
      </Paper>
    </Container>
  );
}
