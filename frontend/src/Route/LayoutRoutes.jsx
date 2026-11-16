import React from 'react';
import { Route, Routes } from 'react-router-dom';
import { routes } from './Routes';
import AppLayout from '../Layout/Layout';
import NotFound from '../Components/NotFound';

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
      {/* Unknown addresses keep the app shell so people can navigate away. */}
      <Route element={<AppLayout notFound />}>
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
};

export default LayoutRoutes;
