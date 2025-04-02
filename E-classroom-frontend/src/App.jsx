import {  Routes, Route, Outlet } from 'react-router-dom';
import { Provider } from 'react-redux';
import { store } from './store/store';

import Layout from './components/Layout';
import PrivateRoute from './components/PrivateRoute';
import Landing from './pages/Landing';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Classes from './pages/Classes';
import ClassDetails from './pages/ClassDetails';
import Lectures from './pages/Lectures';
import Assignments from './pages/Assignments';
import Settings from './pages/Settings';
import Announcement from './pages/Announcement';

function App() {
  return (
  <Provider store={store}>  
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route element={<Layout />}>
        <Route element={<PrivateRoute><Outlet /></PrivateRoute>}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/classes" element={<Classes />} />
          <Route path="/classes/:classId" element={<ClassDetails />} />
          <Route path="/classes/:classId/lectures" element={<Lectures />} />
          <Route path="/classes/:classId/assignments" element={<Assignments />} />
          <Route path="/classes/:classId/announcement" element={<Announcement />} />
          <Route path="/settings" element={<Settings />} />
        </Route>
      </Route>
    </Routes>
  </Provider>
  );
}

export default App;