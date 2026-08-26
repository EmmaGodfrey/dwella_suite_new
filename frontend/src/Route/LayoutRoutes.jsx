import React from 'react';
import { Route, Routes } from 'react-router-dom';
import { routes } from './Routes';
import AppLayout from '../Layout/Layout';

const LayoutRoutes = () => {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        {routes.map(({ path, Component, title, description }) => (
          <Route
            path={path}
            element={React.cloneElement(Component, { routeTitle: title, routeDescription: description })}
            key={path}
          />
        ))}
      </Route>
    </Routes>
  );
};

export default LayoutRoutes;
