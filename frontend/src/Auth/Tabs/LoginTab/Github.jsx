/* eslint-disable no-unused-vars */
import React, { Fragment, useState, useEffect } from "react";
import { GitHub } from "react-feather";
import { Btn } from "../../../AbstractElements";
import { useNavigate } from "react-router-dom";
import man from "/assets/images/dashboard/1.png";

const GithubCus = () => {
  const history = useNavigate();

  const [value, setValue] = useState(localStorage.getItem("profileURL" || man));
  const [name, setName] = useState(localStorage.getItem("Name"));

  useEffect(() => {
    localStorage.setItem("profileURL", value);
    localStorage.setItem("Name", name);
  }, [value, name]);
  const githubAuth = async () => {
    history(`/pages/sample-page`);
  };
  return (
    <Fragment>
      <Btn attrBtn={{ color: "light", onClick: githubAuth }}>
        <GitHub />
      </Btn>
    </Fragment>
  );
};

export default GithubCus;
