import React from "react";
import ReactDOM from "react-dom/client";
import "./index.scss";
import "./i18n";
import App from "./App";
import reportWebVitals from "./reportWebVitals";
import { unstable_batchedUpdates } from "react-dom";
// unstable_batchedUpdates(() => {
//   console.error = () => {};
// });

class ErrorBoundary extends React.Component {
  componentDidCatch(error) {
    if (error.message.includes("ToastContainer")) {
      return;
    }
  }

  render() {
    return this.props.children;
  }
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <ErrorBoundary>
    <App />
  </ErrorBoundary>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
