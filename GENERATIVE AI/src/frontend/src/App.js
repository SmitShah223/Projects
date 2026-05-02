import React, {useState} from "react";
import "./styles/App.css";
import { Container, Paper, Box, Typography, Grid, TextField, IconButton, Button} from "@material-ui/core";
import { makeStyles } from "@material-ui/core/styles";
import DeleteOutlineIcon from '@material-ui/icons/DeleteOutline';

/*
import './PDFViewer.css'
import File from './pdf.worker.min.js';
import { Viewer, Worker} from '@react-pdf-viewer/default-layout';
import { defaultLayoutPlugin } from '@react-pdf-viewer/default-layout';
import '@react-pdf-viewer/core/lib/styles/index.js'
import '@react-pdf-viewer/default-layout/lib/styles/index.css'
*/

const useStyles = makeStyles((theme) => ({
  root: {
    width: "100vw",
    height: "100vh",
    backgroundColor: theme.palette.grey[300],
    paddingTop: theme.spacing(5),
  },
  subjGroup: {
    marginBottom: theme.spacing(3)
  },
  buttonGroup: {
    marginLeft: theme.spacing(2)
  },
  inputGroup: {
    marginBottom: theme.spacing(1)
  }
}));

function App() {
  const classes = useStyles();
  const userTemplate = {"name": "", "subtopics": "", "remarks": ""};
  const [users, setUsers] = useState([userTemplate]);
  const [subject, setSubject] = useState();
  const addUser = () => {
    setUsers([...users, userTemplate])
  };

  const onChange = (e, index) => {
    const updatedUsers = users.map((user, i) => 
      index == i 
        ? Object.assign(user, {[e.target.name]: e.target.value})
        : user
    );
    setUsers(updatedUsers);
  };

  const removeUser = (index) => {
    const filteredUsers = [...users];
    filteredUsers.splice(index, 1);
    setUsers(filteredUsers);
  };

  const submit = () => {
    var modules = JSON.stringify(users)

    var payload = {
      "subject" : subject,
      "modules" : modules
    }

    console.log(payload)
  }

  return (
    <Container className={classes.root}>
      <Paper component={Box} p={4}>
        <TextField
          label="Subject"
          placeholder="Enter subject name"
          variant="outlined"
          name="subject"
          onChange={(e)=> setSubject(e.target.value)}
          className={classes.subjGroup}
          required
        />
        {users.map((user, index) => (
          <Grid container spacing={3} key={index} className={classes.inputGroup}>
            <Grid item md={4}>
              <TextField
                label="Module/Chapter"
                placeholder="Enter name of module"
                variant="outlined"
                name="name"
                onChange={e => onChange(e, index)}
                value={user.name}
                fullWidth
                required
              />
            </Grid>
            <Grid item md={4}>
              <TextField
                label="Subtopics"
                placeholder="Enter Comma-separated subtopic name"
                variant="outlined"
                name="subtopics"
                onChange={e => onChange(e, index)}
                value={user.subtopics}
                fullWidth
                required
              />
            </Grid>
            <Grid item md={3}>
              <TextField
                label="Remarks"
                placeholder="Enter special remarks"
                variant="outlined"
                name="remarks"
                onChange={e => onChange(e, index)}
                value={user.remarks}
                fullWidth
                required
              />
            </Grid>
            <Grid item md={1}>
              <IconButton color="secondary" onClick={() => removeUser(index)}>
                <DeleteOutlineIcon/>
              </IconButton>
            </Grid>
          </Grid>
        ))}
        <Button variant="contained" color="primary" onClick={addUser}>Add module</Button>
        <Button variant="contained" color="primary" className={classes.buttonGroup} onClick={submit}>Submit</Button>
      </Paper>
    </Container>
  );
};

export default App;
