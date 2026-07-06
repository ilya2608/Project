import {
  Box,
  Button,
  Card,
  CardContent,
  Checkbox,
  Container,
  FormControlLabel,
  MenuItem,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useEffect, useState } from "react";
import { availabilityApi } from "../../api/availability";
import type { AvailabilityException, WeeklyRule } from "../../api/types";
import { useAuth } from "../../auth/AuthContext";

const WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

export function AvailabilityEditorPage() {
  const { user } = useAuth();
  const doctorId = user!.id;

  const [rules, setRules] = useState<WeeklyRule[]>([]);
  const [exceptions, setExceptions] = useState<AvailabilityException[]>([]);

  const [newRule, setNewRule] = useState({ weekday: 0, start_time: "09:00", end_time: "12:00" });
  const [newException, setNewException] = useState({
    date: "",
    is_full_day_block: true,
    start_time: "",
    end_time: "",
    reason: "",
  });

  const load = () => {
    availabilityApi.listRules(doctorId).then(setRules);
    availabilityApi.listExceptions(doctorId).then(setExceptions);
  };

  useEffect(() => {
    load();
  }, [doctorId]);

  const addRule = async () => {
    await availabilityApi.createRule(doctorId, {
      weekday: newRule.weekday,
      start_time: newRule.start_time,
      end_time: newRule.end_time,
      valid_from: null,
      valid_until: null,
    });
    load();
  };

  const removeRule = async (ruleId: string) => {
    await availabilityApi.deleteRule(doctorId, ruleId);
    load();
  };

  const addException = async () => {
    await availabilityApi.createException(doctorId, {
      date: newException.date,
      kind: "block",
      is_full_day_block: newException.is_full_day_block,
      start_time: newException.is_full_day_block ? null : newException.start_time || null,
      end_time: newException.is_full_day_block ? null : newException.end_time || null,
      reason: newException.reason || null,
    });
    load();
  };

  const removeException = async (exceptionId: string) => {
    await availabilityApi.deleteException(doctorId, exceptionId);
    load();
  };

  return (
    <Container maxWidth="md" sx={{ mt: 4 }}>
      <Typography variant="h5" gutterBottom>
        Weekly availability
      </Typography>
      <Stack spacing={1} sx={{ mb: 3 }}>
        {rules.map((rule) => (
          <Card key={rule.id} variant="outlined">
            <CardContent sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <Typography>
                {WEEKDAYS[rule.weekday]}: {rule.start_time.slice(0, 5)} – {rule.end_time.slice(0, 5)}
              </Typography>
              <Button color="error" size="small" onClick={() => removeRule(rule.id)}>
                Remove
              </Button>
            </CardContent>
          </Card>
        ))}
      </Stack>

      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Typography variant="subtitle1" gutterBottom>
            Add a weekly working block
          </Typography>
          <Stack direction="row" spacing={2} alignItems="center" flexWrap="wrap">
            <TextField
              select
              label="Day"
              value={newRule.weekday}
              onChange={(e) => setNewRule({ ...newRule, weekday: Number(e.target.value) })}
              sx={{ minWidth: 140 }}
            >
              {WEEKDAYS.map((day, i) => (
                <MenuItem key={day} value={i}>
                  {day}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              label="Start"
              type="time"
              value={newRule.start_time}
              onChange={(e) => setNewRule({ ...newRule, start_time: e.target.value })}
            />
            <TextField
              label="End"
              type="time"
              value={newRule.end_time}
              onChange={(e) => setNewRule({ ...newRule, end_time: e.target.value })}
            />
            <Button variant="contained" onClick={addRule}>
              Add
            </Button>
          </Stack>
        </CardContent>
      </Card>

      <Typography variant="h5" gutterBottom>
        Time off / one-off blocks
      </Typography>
      <Stack spacing={1} sx={{ mb: 3 }}>
        {exceptions.map((exc) => (
          <Card key={exc.id} variant="outlined">
            <CardContent sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <Typography>
                {exc.date} {exc.is_full_day_block ? "(full day)" : `${exc.start_time?.slice(0, 5)}–${exc.end_time?.slice(0, 5)}`}
                {exc.reason ? ` — ${exc.reason}` : ""}
              </Typography>
              <Button color="error" size="small" onClick={() => removeException(exc.id)}>
                Remove
              </Button>
            </CardContent>
          </Card>
        ))}
      </Stack>

      <Card>
        <CardContent>
          <Typography variant="subtitle1" gutterBottom>
            Block out time
          </Typography>
          <Stack direction="row" spacing={2} alignItems="center" flexWrap="wrap">
            <TextField
              label="Date"
              type="date"
              value={newException.date}
              onChange={(e) => setNewException({ ...newException, date: e.target.value })}
            />
            <FormControlLabel
              control={
                <Checkbox
                  checked={newException.is_full_day_block}
                  onChange={(e) => setNewException({ ...newException, is_full_day_block: e.target.checked })}
                />
              }
              label="Full day"
            />
            {!newException.is_full_day_block && (
              <>
                <TextField
                  label="Start"
                  type="time"
                  value={newException.start_time}
                  onChange={(e) => setNewException({ ...newException, start_time: e.target.value })}
                />
                <TextField
                  label="End"
                  type="time"
                  value={newException.end_time}
                  onChange={(e) => setNewException({ ...newException, end_time: e.target.value })}
                />
              </>
            )}
            <TextField
              label="Reason"
              value={newException.reason}
              onChange={(e) => setNewException({ ...newException, reason: e.target.value })}
            />
            <Box>
              <Button variant="contained" onClick={addException} disabled={!newException.date}>
                Add
              </Button>
            </Box>
          </Stack>
        </CardContent>
      </Card>
    </Container>
  );
}
