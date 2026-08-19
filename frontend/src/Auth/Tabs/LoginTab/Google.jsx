/* eslint-disable no-unused-vars */
import React, { Fragment, useState, useEffect } from "react";
import { Btn } from "../../../AbstractElements";
import { useNavigate } from "react-router-dom";
import man from "/assets/images/dashboard/1.png";

const GoogleCus = () => {
  const history = useNavigate();

  const [value, setValue] = useState(localStorage.getItem("profileURL" || man));
  const [name, setName] = useState(localStorage.getItem("Name"));

  useEffect(() => {
    localStorage.setItem("profileURL", value);
    localStorage.setItem("Name", name);
  }, [value, name]);

  const googleAuth = async () => {
    history(`/pages/sample-page`);
  };

  return (
    <Fragment>
      <Btn attrBtn={{ color: "light", onClick: googleAuth }}>
        <i className="fa fa-google txt-googleplus"></i>
      </Btn>
    </Fragment>
  );
};

export default GoogleCus;
