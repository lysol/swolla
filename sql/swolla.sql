--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: contacts; Type: TABLE; Schema: public; Owner: swolla; Tablespace: 
--

CREATE TABLE contacts (
    user_id character varying,
    contact_id character varying NOT NULL,
    short_name character varying
);


ALTER TABLE public.contacts OWNER TO swolla;

--
-- Name: user_credentials; Type: TABLE; Schema: public; Owner: swolla; Tablespace: 
--

CREATE TABLE user_credentials (
    user_id character varying NOT NULL,
    code character varying NOT NULL,
    access_token character varying NOT NULL,
    phone_number character varying
);


ALTER TABLE public.user_credentials OWNER TO swolla;

--
-- Name: contacts_pkey; Type: CONSTRAINT; Schema: public; Owner: swolla; Tablespace: 
--

ALTER TABLE ONLY contacts
    ADD CONSTRAINT contacts_pkey PRIMARY KEY (contact_id);


--
-- Name: user_credentials_pkey; Type: CONSTRAINT; Schema: public; Owner: swolla; Tablespace: 
--

ALTER TABLE ONLY user_credentials
    ADD CONSTRAINT user_credentials_pkey PRIMARY KEY (user_id);


--
-- Name: public; Type: ACL; Schema: -; Owner: swolla
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM swolla;
GRANT ALL ON SCHEMA public TO swolla;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--

