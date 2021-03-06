import React, { Component } from "react";
import { FormErrors } from "./FormErrors";
import "./Form.css";
import { io } from "socket.io-client";

class Form extends Component {
  constructor(props) {
    super(props);
    this.state = {
      socket: "",
      socketStatus: false,
      keyword: "",
      url: "",
      source_len: 200,
      time: 2,
      text_len: 30,
      urls: [],
      search_sys: "google",
      format: "txt",
      formErrors: {
        url: "",
        keyword: "",
        source_len: "",
        time: "",
        text_len: "",
      },
      UrlValid: false,
      keywordValid: false,
      Source_lenValid: true,
      timeValid: true,
      text_lenValid: true,
      formValid: false,
      parse_type: "",
      is_compared: false,
      textvalue: "",
    };
  }
  componentWillUnmount() {
    this.socket.close();
    console.log("component unmounted");
  }
  componentDidMount() {
    var sensorEndpoint = "https://webcleaner.herokuapp.com/";
    this.socket = io.connect(sensorEndpoint, {
      reconnection: true,
      transports: ["websocket"],
    });
    console.log("component mounted");
    this.socket.on("responseMessage", (message) => {
      this.setState({ textvalue: message.data });

      console.log("responseMessage", message);
    });
    this.socket.on("Message", (message) => {
      console.log("responseMessage", message);
    });
  }
  handleEmit = (event) => {
    event.preventDefault();
    this.socket.emit("message", {
      data: {
        keyword: this.state.keyword,
        source_len: this.state.source_len,
        time: this.state.time,
        text_len: this.state.text_len,
        urls: this.state.urls,
        is_compared: this.state.is_compared,
        browser: this.state.search_sys,
        parse_type: this.state.parse_type,
      },
      status: "On",
    });
    this.setState({ socketStatus: "On" });

    console.log("Emit Clicked");
  };
  handleUserInput = (e) => {
    const name = e.target.name;
    const value = e.target.value;
    this.setState({ [name]: value }, () => {
      this.validateField(name, value);
    });
  };

  validateField(fieldName, value) {
    let fieldValidationErrors = this.state.formErrors;
    let UrlValid = this.state.UrlValid;
    let keywordValid = this.state.keywordValid;
    let Source_lenValid = this.state.Source_lenValid;
    let timeValid = this.state.timeValid;
    let textlenValid = this.state.text_lenValid;
    switch (fieldName) {
      case "url":
        UrlValid = value.match(
          /(ftp|http|https):\/\/(\w+:{0,1}\w*@)?(\S+)(:[0-9]+)?(\/|\/([\w#!:.?+=&%@!\-/]))?/
        );
        fieldValidationErrors.url = UrlValid ? "" : " is invalid";
        break;
      case "keyword":
        keywordValid = value.length >= 2 && value.length <= 50;
        fieldValidationErrors.keyword = keywordValid
          ? ""
          : "incorrect length (must be from 2 to 50)";
        break;
      case "source_len":
        Source_lenValid = value.match(/[0-9]/) && value > 0 && value <= 300;
        fieldValidationErrors.source_len = Source_lenValid
          ? ""
          : "it must be integer from 1 to 300";
        break;
      case "time":
        timeValid = value > 0.5 && value < 30;
        fieldValidationErrors.time = timeValid
          ? ""
          : "invalid time (must be from 0.5 to 30)";
        break;
      case "text_len":
        textlenValid = value >= 30 && value.match(/[0-9]/);
        fieldValidationErrors.text_len = textlenValid
          ? ""
          : "invalid text len (must be 30 or more)";
        break;
      default:
        break;
    }
    this.setState(
      {
        formErrors: fieldValidationErrors,
        UrlValid: UrlValid,
        keywordValid: keywordValid,
        timeValid: timeValid,
        Source_lenValid: Source_lenValid,
        text_lenValid: textlenValid,
      },
      this.validateForm
    );
  }

  validateForm() {
    this.setState({
      formValid:
        ((this.state.keywordValid &&
          this.state.Source_lenValid &&
          this.state.parse_type === "keyword") ||
          (this.state.urls.length > 0 && this.state.parse_type === "urlist")) &&
        this.state.text_lenValid &&
        this.state.timeValid &&
        this.state.is_compared.length > 0,
    });
  }

  errorClass(error) {
    return error.length === 0 ? "" : "has-error";
  }
  onChangeValue(event) {
    console.log(event.target.value);
    this.setState(
      { [event.target.name]: event.target.value },
      this.validateForm
    );
    console.log(this.state);
  }
  addUrl(event) {
    event.preventDefault();
    this.setState(
      { urls: [...this.state.urls, this.state.url], url: "" },
      this.validateForm
    );
  }
  onKeyDown = (event) => {
    if (event.keyCode === 9) {
      event.preventDefault();
      const { selectionStart, selectionEnd } = event.target;
      this.setState((prevState) => ({
        textvalue:
          prevState.textvalue.substring(0, selectionStart) +
          "\t" +
          prevState.textvalue.substring(selectionEnd),
      }));
    }
  };
  download = () => {
    let element = document.createElement("a");
    let format;
    let text;
    if (this.state.format === "txt") {
      format = "data:text/plain;charset=utf-8,";
      text = this.state.textvalue;
    } else {
      format = "data:text/json;charset=utf-8,";
      text = this.state.textvalue.split("\n\n\n");
      let splited = text.map((x) => {
        let a = x.split("\n", 2);
        let b = a[0].split("\t", 2);
        return [b, a[1]];
      });
      let json = splited.map((x, index) => {
        return {
          source:
            x[0][0].split(" ", 2)[1] === undefined
              ? ""
              : x[0][0].split(" ", 2)[1],
          certainty: x[0].length === 2 ? x[0][1].split(" ", 2)[1] : "",
          texts:
            x[1] === undefined
              ? typeof text === "object" && text.length >= 2
                ? text[index]
                : text
              : x[1],
        };
      });
      text = JSON.stringify(json);
    }
    element.setAttribute("href", format + encodeURIComponent(text));
    element.setAttribute("download", "CollectedData." + this.state.format);

    element.style.display = "none";
    document.body.appendChild(element);

    element.click();

    document.body.removeChild(element);
  };

  render() {
    return (
      <div className="webapp">
        <form className="demoForm">
          <h2>???????? ????????????????????</h2>
          <div className="panel panel-default">
            <FormErrors formErrors={this.state.formErrors} />
          </div>

          <div
            onChange={this.onChangeValue.bind(this)}
            className="rad parse_type"
          >
            <input
              type="radio"
              value="urlist"
              name="parse_type"
              className="type_radio"
            />
            ???????? ?? ???????????????? ???????????????? ????????????
            <input
              type="radio"
              value="keyword"
              name="parse_type"
              className="type_radio"
            />
            ???????? ???? ???????????????? ????????????
          </div>

          {this.state.parse_type === "keyword" ? (
            <div className="keyword_arg">
              <div
                className={`form-group ${this.errorClass(
                  this.state.formErrors.keyword
                )}`}
              ></div>
              <label htmlFor="keyword">?????????????? ??????????:</label>
              <input
                type="text"
                className={
                  this.state.formErrors.keyword.length === 0
                    ? "form-control"
                    : "form-control invalid"
                }
                name="keyword"
                placeholder="Keyword"
                value={this.state.keyword}
                onChange={this.handleUserInput}
              />
              <label htmlFor="source_len">?????????????????????? ?????????????????? ????????????:</label>
              <input
                type="number"
                className={
                  this.state.formErrors.source_len.length === 0
                    ? "form-control"
                    : "form-control invalid"
                }
                name="source_len"
                placeholder="Amount"
                value={this.state.source_len}
                onChange={this.handleUserInput}
              />
              <label htmlFor="search_sys">???????????????? ??????????????:</label>
              <select
                className="search_sys"
                defaultValue="google"
                name="search_sys"
                onChange={this.handleUserInput}
              >
                <option value="google">Google</option>
                <option value="Bing">Bing</option>
              </select>
            </div>
          ) : (
            ""
          )}
          {this.state.parse_type === "urlist" ? (
            <div>
              <div>???????????? ???????????????????? ??????????:</div>
              <div
                className={`form-group ${this.errorClass(
                  this.state.formErrors.url
                )}`}
              ></div>
              {this.state.urls.map((url) => (
                <div key={url}> {url}</div>
              ))}
              <label htmlFor="url">???????????? url ????????????: </label>
              <input
                type="text"
                className={
                  this.state.formErrors.url.length === 0
                    ? "form-control"
                    : "form-control invalid"
                }
                name="url"
                placeholder="Url"
                value={this.state.url}
                onChange={this.handleUserInput}
              />
              <button
                className="btn btn-primary"
                disabled={!this.state.UrlValid}
                onClick={this.addUrl.bind(this)}
              >
                ???????????? ????????????
              </button>
            </div>
          ) : (
            ""
          )}
          <div className="keyword_arg">
            <label htmlFor="time">???????????????????????? ?????? ???????????????? ????????????????:</label>
            <input
              type="number"
              className={
                this.state.formErrors.time.length === 0
                  ? "form-control"
                  : "form-control invalid"
              }
              name="time"
              placeholder="time in seconds"
              value={this.state.time}
              onChange={this.handleUserInput}
            />
            <label htmlFor="text_len">
              ???????????????????? ?????????????????? ???????????? ???? ????????????????:
            </label>
            <input
              type="number"
              className={
                this.state.formErrors.text_len.length === 0
                  ? "form-control"
                  : "form-control invalid"
              }
              name="text_len"
              placeholder="min amount of symbols"
              value={this.state.text_len}
              onChange={this.handleUserInput}
            />
            <label htmlFor="rad">
              ???? ???????????????? ?????????????????????? ?????? ?????????????????? ?????????????????????:
            </label>
            <div onChange={this.onChangeValue.bind(this)} className="rad">
              <input
                type="radio"
                value="yes"
                name="is_compared"
                className="type_radio"
              />
              ??????
              <input
                type="radio"
                value="no"
                name="is_compared"
                className="type_radio"
              />
              ????
            </div>
            <button
              type="submit"
              onClick={this.handleEmit}
              className="btn btn-primary"
              disabled={!this.state.formValid}
            >
              ???????? ????????????????????
            </button>
          </div>
        </form>
        <div className="InfoStatus"></div>
        <label htmlFor="rad">?????????????? ????????????????????:</label>
        <textarea
          className="redactor"
          value={this.state.textvalue}
          name="textvalue"
          onChange={this.handleUserInput}
          onKeyDown={this.onKeyDown}
        />
        <label htmlFor="format">???????????? ????????????????????:</label>
        <select
          className="format"
          defaultValue="txt"
          name="format"
          onChange={this.handleUserInput}
        >
          <option value="txt">txt</option>
          <option value="json">json</option>
        </select>
        <button
          type="submit"
          className="btn btn-primary"
          onClick={this.download}
        >
          ?????????????????????? ????????????????????
        </button>
      </div>
    );
  }
}

export default Form;
