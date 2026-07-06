import { Navigate, Route, Routes } from "react-router-dom";
import { NavBar } from "./components/NavBar";
import { RequireRole } from "./auth/RequireRole";
import { LoginPage } from "./pages/LoginPage";
import { StaffLoginPage } from "./pages/StaffLoginPage";
import { DoctorListPage } from "./pages/patient/DoctorListPage";
import { DoctorDetailBookingPage } from "./pages/patient/DoctorDetailBookingPage";
import { MyAppointmentsPage } from "./pages/patient/MyAppointmentsPage";
import { DoctorAgendaPage } from "./pages/doctor/DoctorAgendaPage";
import { AvailabilityEditorPage } from "./pages/doctor/AvailabilityEditorPage";
import { AdminDoctorsPage } from "./pages/admin/AdminDoctorsPage";
import { AdminDoctorFormPage } from "./pages/admin/AdminDoctorFormPage";
import { AdminAppointmentsPage } from "./pages/admin/AdminAppointmentsPage";

export default function App() {
  return (
    <>
      <NavBar />
      <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/staff-login" element={<StaffLoginPage />} />

        <Route
          path="/patient/doctors"
          element={
            <RequireRole roles={["patient"]}>
              <DoctorListPage />
            </RequireRole>
          }
        />
        <Route
          path="/patient/doctors/:doctorId"
          element={
            <RequireRole roles={["patient"]}>
              <DoctorDetailBookingPage />
            </RequireRole>
          }
        />
        <Route
          path="/patient/appointments"
          element={
            <RequireRole roles={["patient"]}>
              <MyAppointmentsPage />
            </RequireRole>
          }
        />

        <Route
          path="/doctor/agenda"
          element={
            <RequireRole roles={["doctor"]}>
              <DoctorAgendaPage />
            </RequireRole>
          }
        />
        <Route
          path="/doctor/availability"
          element={
            <RequireRole roles={["doctor"]}>
              <AvailabilityEditorPage />
            </RequireRole>
          }
        />

        <Route
          path="/admin/doctors"
          element={
            <RequireRole roles={["admin"]}>
              <AdminDoctorsPage />
            </RequireRole>
          }
        />
        <Route
          path="/admin/doctors/new"
          element={
            <RequireRole roles={["admin"]}>
              <AdminDoctorFormPage />
            </RequireRole>
          }
        />
        <Route
          path="/admin/doctors/:doctorId/edit"
          element={
            <RequireRole roles={["admin"]}>
              <AdminDoctorFormPage />
            </RequireRole>
          }
        />
        <Route
          path="/admin/appointments"
          element={
            <RequireRole roles={["admin"]}>
              <AdminAppointmentsPage />
            </RequireRole>
          }
        />

        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </>
  );
}
