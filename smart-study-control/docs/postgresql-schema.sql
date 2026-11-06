-- Generated PostgreSQL schema reference; deploy with Alembic, not this file.

CREATE TABLE roles (
	name VARCHAR(24) NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);

CREATE INDEX ix_roles_created_at ON roles (created_at);

CREATE TABLE telegram_updates (
	update_id VARCHAR(30) NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (update_id)
);

CREATE INDEX ix_telegram_updates_created_at ON telegram_updates (created_at);

CREATE TABLE users (
	login VARCHAR(80), 
	must_change_password BOOLEAN DEFAULT '0' NOT NULL, 
	auth_epoch INTEGER DEFAULT '0' NOT NULL, 
	email VARCHAR(254) NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	role VARCHAR(24) NOT NULL, 
	active BOOLEAN NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (role IN ('STUDENT','PARENT','TEACHER','SCHOOL_ADMIN','SUPER_ADMIN')), 
	UNIQUE (email)
);

CREATE INDEX ix_users_created_at ON users (created_at);

CREATE UNIQUE INDEX ix_users_login ON users (login);

CREATE INDEX ix_users_role ON users (role);

CREATE TABLE alarms (
	student_id VARCHAR(36) NOT NULL, 
	hour INTEGER NOT NULL, 
	minute INTEGER NOT NULL, 
	weekdays JSON NOT NULL, 
	enabled BOOLEAN NOT NULL, 
	label VARCHAR(100) NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (hour >= 0 AND hour < 24 AND minute >= 0 AND minute < 60), 
	FOREIGN KEY(student_id) REFERENCES users (id)
);

CREATE INDEX ix_alarms_created_at ON alarms (created_at);

CREATE INDEX ix_alarms_student_id ON alarms (student_id);

CREATE TABLE audit_events (
	actor_id VARCHAR(36) NOT NULL, 
	action VARCHAR(100) NOT NULL, 
	resource_id VARCHAR(100) NOT NULL, 
	details JSON NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(actor_id) REFERENCES users (id)
);

CREATE INDEX ix_audit_events_action ON audit_events (action);

CREATE INDEX ix_audit_events_actor_id ON audit_events (actor_id);

CREATE INDEX ix_audit_events_created_at ON audit_events (created_at);

CREATE INDEX ix_audit_events_resource_id ON audit_events (resource_id);

CREATE TABLE auth_challenges (
	user_id VARCHAR(36) NOT NULL, 
	kind VARCHAR(30) NOT NULL, 
	state_hash VARCHAR(64) NOT NULL, 
	verifier_hash VARCHAR(64) NOT NULL, 
	code_hash VARCHAR(64), 
	attempts INTEGER NOT NULL, 
	consumed BOOLEAN NOT NULL, 
	delivered BOOLEAN NOT NULL, 
	payload JSON NOT NULL, 
	expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (attempts >= 0 AND attempts <= 5), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	UNIQUE (state_hash)
);

CREATE INDEX ix_auth_challenges_created_at ON auth_challenges (created_at);

CREATE INDEX ix_auth_challenges_expires_at ON auth_challenges (expires_at);

CREATE INDEX ix_auth_challenges_user_id ON auth_challenges (user_id);

CREATE TABLE automation_runs (
	child_id VARCHAR(36) NOT NULL, 
	guardian_id VARCHAR(36) NOT NULL, 
	day VARCHAR(10) NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	attempts INTEGER DEFAULT '0' NOT NULL, 
	result JSON NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (child_id, day), 
	CHECK (attempts >= 0 AND attempts <= 3), 
	FOREIGN KEY(child_id) REFERENCES users (id), 
	FOREIGN KEY(guardian_id) REFERENCES users (id)
);

CREATE INDEX ix_automation_runs_child_id ON automation_runs (child_id);

CREATE INDEX ix_automation_runs_created_at ON automation_runs (created_at);

CREATE INDEX ix_automation_runs_guardian_id ON automation_runs (guardian_id);

CREATE TABLE automation_settings (
	child_id VARCHAR(36) NOT NULL, 
	guardian_id VARCHAR(36) NOT NULL, 
	enabled BOOLEAN NOT NULL, 
	auto_practice BOOLEAN NOT NULL, 
	daily_reward_limit INTEGER NOT NULL, 
	max_tasks_per_day INTEGER NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (daily_reward_limit >= 0 AND daily_reward_limit <= 120 AND max_tasks_per_day >= 0 AND max_tasks_per_day <= 3), 
	UNIQUE (child_id), 
	FOREIGN KEY(child_id) REFERENCES users (id), 
	FOREIGN KEY(guardian_id) REFERENCES users (id)
);

CREATE INDEX ix_automation_settings_created_at ON automation_settings (created_at);

CREATE INDEX ix_automation_settings_guardian_id ON automation_settings (guardian_id);

CREATE TABLE consent_records (
	actor_id VARCHAR(36) NOT NULL, 
	child_id VARCHAR(36) NOT NULL, 
	purpose VARCHAR(100) NOT NULL, 
	version VARCHAR(20) NOT NULL, 
	granted BOOLEAN NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(actor_id) REFERENCES users (id), 
	FOREIGN KEY(child_id) REFERENCES users (id)
);

CREATE INDEX ix_consent_records_actor_id ON consent_records (actor_id);

CREATE INDEX ix_consent_records_child_id ON consent_records (child_id);

CREATE INDEX ix_consent_records_created_at ON consent_records (created_at);

CREATE TABLE deletion_requests (
	user_id VARCHAR(36) NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_deletion_requests_created_at ON deletion_requests (created_at);

CREATE INDEX ix_deletion_requests_user_id ON deletion_requests (user_id);

CREATE TABLE devices (
	student_id VARCHAR(36) NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	mode VARCHAR(24) NOT NULL, 
	version INTEGER NOT NULL, 
	deprovision_requested BOOLEAN NOT NULL, 
	retired BOOLEAN NOT NULL, 
	compliance JSON NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(student_id) REFERENCES users (id)
);

CREATE INDEX ix_devices_created_at ON devices (created_at);

CREATE INDEX ix_devices_student_id ON devices (student_id);

CREATE TABLE families (
	owner_id VARCHAR(36) NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(owner_id) REFERENCES users (id)
);

CREATE INDEX ix_families_created_at ON families (created_at);

CREATE INDEX ix_families_owner_id ON families (owner_id);

CREATE TABLE focus_sessions (
	student_id VARCHAR(36) NOT NULL, 
	subject VARCHAR(100) NOT NULL, 
	duration_seconds INTEGER NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	completed_at TIMESTAMP WITHOUT TIME ZONE, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(student_id) REFERENCES users (id)
);

CREATE INDEX ix_focus_sessions_created_at ON focus_sessions (created_at);

CREATE INDEX ix_focus_sessions_student_id ON focus_sessions (student_id);

CREATE TABLE invites (
	owner_id VARCHAR(36) NOT NULL, 
	kind VARCHAR(20) NOT NULL, 
	resource_id VARCHAR(36) NOT NULL, 
	code_hash VARCHAR(64) NOT NULL, 
	expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	used BOOLEAN NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(owner_id) REFERENCES users (id), 
	UNIQUE (code_hash)
);

CREATE INDEX ix_invites_created_at ON invites (created_at);

CREATE INDEX ix_invites_owner_id ON invites (owner_id);

CREATE TABLE location_consents (
	child_id VARCHAR(36) NOT NULL, 
	guardian_id VARCHAR(36) NOT NULL, 
	enabled BOOLEAN NOT NULL, 
	max_minutes INTEGER NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (max_minutes >= 1 AND max_minutes <= 240), 
	UNIQUE (child_id), 
	FOREIGN KEY(child_id) REFERENCES users (id), 
	FOREIGN KEY(guardian_id) REFERENCES users (id)
);

CREATE INDEX ix_location_consents_created_at ON location_consents (created_at);

CREATE INDEX ix_location_consents_guardian_id ON location_consents (guardian_id);

CREATE TABLE location_shares (
	child_id VARCHAR(36) NOT NULL, 
	consent_guardian_id VARCHAR(36) NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	latitude FLOAT, 
	longitude FLOAT, 
	accuracy_m FLOAT, 
	received_at TIMESTAMP WITHOUT TIME ZONE, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (latitude IS NULL OR (latitude >= -90 AND latitude <= 90)), 
	CHECK (longitude IS NULL OR (longitude >= -180 AND longitude <= 180)), 
	CHECK (accuracy_m IS NULL OR (accuracy_m >= 0 AND accuracy_m <= 100000)), 
	FOREIGN KEY(child_id) REFERENCES users (id), 
	FOREIGN KEY(consent_guardian_id) REFERENCES users (id)
);

CREATE INDEX ix_location_shares_child_id ON location_shares (child_id);

CREATE INDEX ix_location_shares_created_at ON location_shares (created_at);

CREATE INDEX ix_location_shares_expires_at ON location_shares (expires_at);

CREATE TABLE notifications (
	user_id VARCHAR(36) NOT NULL, 
	title VARCHAR(150) NOT NULL, 
	body TEXT NOT NULL, 
	read BOOLEAN NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_notifications_created_at ON notifications (created_at);

CREATE INDEX ix_notifications_user_id ON notifications (user_id);

CREATE TABLE parent_child_links (
	parent_id VARCHAR(36) NOT NULL, 
	child_id VARCHAR(36) NOT NULL, 
	consent BOOLEAN NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (parent_id, child_id), 
	FOREIGN KEY(parent_id) REFERENCES users (id), 
	FOREIGN KEY(child_id) REFERENCES users (id)
);

CREATE INDEX ix_parent_child_links_child_id ON parent_child_links (child_id);

CREATE INDEX ix_parent_child_links_created_at ON parent_child_links (created_at);

CREATE INDEX ix_parent_child_links_parent_id ON parent_child_links (parent_id);

CREATE TABLE passkeys (
	user_id VARCHAR(36) NOT NULL, 
	credential_id VARCHAR(1500) NOT NULL, 
	public_key TEXT NOT NULL, 
	sign_count INTEGER NOT NULL, 
	label VARCHAR(100) NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (sign_count >= 0), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	UNIQUE (credential_id)
);

CREATE INDEX ix_passkeys_created_at ON passkeys (created_at);

CREATE INDEX ix_passkeys_user_id ON passkeys (user_id);

CREATE TABLE refresh_tokens (
	user_id VARCHAR(36) NOT NULL, 
	family VARCHAR(36) NOT NULL, 
	digest VARCHAR(64) NOT NULL, 
	expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	revoked BOOLEAN NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	UNIQUE (digest)
);

CREATE INDEX ix_refresh_tokens_created_at ON refresh_tokens (created_at);

CREATE INDEX ix_refresh_tokens_family ON refresh_tokens (family);

CREATE INDEX ix_refresh_tokens_user_id ON refresh_tokens (user_id);

CREATE TABLE reward_transactions (
	student_id VARCHAR(36) NOT NULL, 
	origin VARCHAR(150) NOT NULL, 
	delta INTEGER NOT NULL, 
	kind VARCHAR(24) NOT NULL, 
	reference VARCHAR(100) NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(student_id) REFERENCES users (id), 
	UNIQUE (origin)
);

CREATE INDEX ix_reward_transactions_created_at ON reward_transactions (created_at);

CREATE INDEX ix_reward_transactions_student_id ON reward_transactions (student_id);

CREATE TABLE reward_wallets (
	student_id VARCHAR(36) NOT NULL, 
	available INTEGER NOT NULL, 
	debt INTEGER NOT NULL, 
	daily_max INTEGER NOT NULL, 
	weekly_max INTEGER NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (available >= 0 AND debt >= 0 AND daily_max >= 0 AND weekly_max >= 0), 
	UNIQUE (student_id), 
	FOREIGN KEY(student_id) REFERENCES users (id)
);

CREATE INDEX ix_reward_wallets_created_at ON reward_wallets (created_at);

CREATE TABLE schools (
	name VARCHAR(120) NOT NULL, 
	owner_id VARCHAR(36) NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(owner_id) REFERENCES users (id)
);

CREATE INDEX ix_schools_created_at ON schools (created_at);

CREATE INDEX ix_schools_owner_id ON schools (owner_id);

CREATE TABLE sleep_schedules (
	student_id VARCHAR(36) NOT NULL, 
	start_minute INTEGER NOT NULL, 
	end_minute INTEGER NOT NULL, 
	timezone VARCHAR(64) NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (start_minute >= 0 AND start_minute < 1440 AND end_minute >= 0 AND end_minute < 1440), 
	UNIQUE (student_id), 
	FOREIGN KEY(student_id) REFERENCES users (id)
);

CREATE INDEX ix_sleep_schedules_created_at ON sleep_schedules (created_at);

CREATE TABLE study_books (
	owner_id VARCHAR(36) NOT NULL, 
	title VARCHAR(150) NOT NULL, 
	filename VARCHAR(180) NOT NULL, 
	storage_key VARCHAR(36) NOT NULL, 
	sha256 VARCHAR(64) NOT NULL, 
	size INTEGER NOT NULL, 
	page_count INTEGER NOT NULL, 
	status VARCHAR(24) NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (size > 0 AND page_count > 0 AND page_count <= 300), 
	UNIQUE (owner_id, sha256), 
	FOREIGN KEY(owner_id) REFERENCES users (id), 
	UNIQUE (storage_key)
);

CREATE INDEX ix_study_books_created_at ON study_books (created_at);

CREATE INDEX ix_study_books_owner_id ON study_books (owner_id);

CREATE TABLE sync_outbox_records (
	user_id VARCHAR(36) NOT NULL, 
	event_type VARCHAR(50) NOT NULL, 
	payload JSON NOT NULL, 
	processed_at TIMESTAMP WITHOUT TIME ZONE, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_sync_outbox_records_created_at ON sync_outbox_records (created_at);

CREATE INDEX ix_sync_outbox_records_user_id ON sync_outbox_records (user_id);

CREATE TABLE telegram_identities (
	user_id VARCHAR(36) NOT NULL, 
	telegram_user_id VARCHAR(30) NOT NULL, 
	chat_id VARCHAR(30) NOT NULL, 
	notifications_enabled BOOLEAN NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (user_id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	UNIQUE (telegram_user_id)
);

CREATE INDEX ix_telegram_identities_created_at ON telegram_identities (created_at);

CREATE TABLE user_roles (
	user_id VARCHAR(36) NOT NULL, 
	role_id VARCHAR(36) NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (user_id, role_id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(role_id) REFERENCES roles (id)
);

CREATE INDEX ix_user_roles_created_at ON user_roles (created_at);

CREATE INDEX ix_user_roles_user_id ON user_roles (user_id);

CREATE TABLE app_unlock_sessions (
	student_id VARCHAR(36) NOT NULL, 
	device_id VARCHAR(36) NOT NULL, 
	package VARCHAR(200) NOT NULL, 
	minutes INTEGER NOT NULL, 
	idempotency_key VARCHAR(100) NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (student_id, idempotency_key), 
	CHECK (minutes > 0 AND minutes <= 120), 
	FOREIGN KEY(student_id) REFERENCES users (id), 
	FOREIGN KEY(device_id) REFERENCES devices (id)
);

CREATE INDEX ix_app_unlock_sessions_created_at ON app_unlock_sessions (created_at);

CREATE INDEX ix_app_unlock_sessions_device_id ON app_unlock_sessions (device_id);

CREATE INDEX ix_app_unlock_sessions_student_id ON app_unlock_sessions (student_id);

CREATE TABLE book_lessons (
	book_id VARCHAR(36) NOT NULL, 
	title VARCHAR(150) NOT NULL, 
	start_page INTEGER NOT NULL, 
	end_page INTEGER NOT NULL, 
	content JSON NOT NULL, 
	source_digest VARCHAR(64) NOT NULL, 
	provider_model VARCHAR(200) NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	version INTEGER NOT NULL, 
	published_by VARCHAR(36), 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (start_page > 0 AND end_page >= start_page AND end_page - start_page < 5), 
	FOREIGN KEY(book_id) REFERENCES study_books (id), 
	FOREIGN KEY(published_by) REFERENCES users (id)
);

CREATE INDEX ix_book_lessons_book_id ON book_lessons (book_id);

CREATE INDEX ix_book_lessons_created_at ON book_lessons (created_at);

CREATE TABLE book_pages (
	book_id VARCHAR(36) NOT NULL, 
	page_number INTEGER NOT NULL, 
	text TEXT NOT NULL, 
	method VARCHAR(20) NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (book_id, page_number), 
	CHECK (page_number > 0), 
	FOREIGN KEY(book_id) REFERENCES study_books (id)
);

CREATE INDEX ix_book_pages_book_id ON book_pages (book_id);

CREATE INDEX ix_book_pages_created_at ON book_pages (created_at);

CREATE TABLE classrooms (
	name VARCHAR(100) NOT NULL, 
	teacher_id VARCHAR(36) NOT NULL, 
	school_id VARCHAR(36), 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(teacher_id) REFERENCES users (id), 
	FOREIGN KEY(school_id) REFERENCES schools (id)
);

CREATE INDEX ix_classrooms_created_at ON classrooms (created_at);

CREATE INDEX ix_classrooms_teacher_id ON classrooms (teacher_id);

CREATE TABLE device_enrollments (
	device_id VARCHAR(36) NOT NULL, 
	authorized_by VARCHAR(36) NOT NULL, 
	consent_id VARCHAR(36) NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(device_id) REFERENCES devices (id), 
	FOREIGN KEY(authorized_by) REFERENCES users (id), 
	FOREIGN KEY(consent_id) REFERENCES consent_records (id)
);

CREATE INDEX ix_device_enrollments_created_at ON device_enrollments (created_at);

CREATE INDEX ix_device_enrollments_device_id ON device_enrollments (device_id);

CREATE TABLE device_policies (
	device_id VARCHAR(36) NOT NULL, 
	version INTEGER NOT NULL, 
	document JSON NOT NULL, 
	actor_id VARCHAR(36) NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (device_id, version), 
	FOREIGN KEY(device_id) REFERENCES devices (id), 
	FOREIGN KEY(actor_id) REFERENCES users (id)
);

CREATE INDEX ix_device_policies_created_at ON device_policies (created_at);

CREATE INDEX ix_device_policies_device_id ON device_policies (device_id);

CREATE TABLE family_members (
	family_id VARCHAR(36) NOT NULL, 
	user_id VARCHAR(36) NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (family_id, user_id), 
	FOREIGN KEY(family_id) REFERENCES families (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_family_members_created_at ON family_members (created_at);

CREATE INDEX ix_family_members_family_id ON family_members (family_id);

CREATE INDEX ix_family_members_user_id ON family_members (user_id);

CREATE TABLE policy_versions (
	device_id VARCHAR(36) NOT NULL, 
	version INTEGER NOT NULL, 
	actor_id VARCHAR(36) NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (device_id, version), 
	FOREIGN KEY(device_id) REFERENCES devices (id), 
	FOREIGN KEY(actor_id) REFERENCES users (id)
);

CREATE INDEX ix_policy_versions_created_at ON policy_versions (created_at);

CREATE INDEX ix_policy_versions_device_id ON policy_versions (device_id);

CREATE TABLE staff_profiles (
	user_id VARCHAR(36) NOT NULL, 
	school_id VARCHAR(36) NOT NULL, 
	created_by VARCHAR(36) NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (user_id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(school_id) REFERENCES schools (id), 
	FOREIGN KEY(created_by) REFERENCES users (id)
);

CREATE INDEX ix_staff_profiles_created_at ON staff_profiles (created_at);

CREATE INDEX ix_staff_profiles_created_by ON staff_profiles (created_by);

CREATE INDEX ix_staff_profiles_school_id ON staff_profiles (school_id);

CREATE TABLE telegram_deliveries (
	notification_id VARCHAR(36) NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	attempts INTEGER NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (attempts >= 0 AND attempts <= 3), 
	UNIQUE (notification_id), 
	FOREIGN KEY(notification_id) REFERENCES notifications (id)
);

CREATE INDEX ix_telegram_deliveries_created_at ON telegram_deliveries (created_at);

CREATE TABLE assignments (
	owner_id VARCHAR(36) NOT NULL, 
	student_id VARCHAR(36) NOT NULL, 
	classroom_id VARCHAR(36), 
	title VARCHAR(150) NOT NULL, 
	subject VARCHAR(100) NOT NULL, 
	description TEXT NOT NULL, 
	due_at TIMESTAMP WITHOUT TIME ZONE, 
	estimated_minutes INTEGER NOT NULL, 
	difficulty VARCHAR(12) NOT NULL, 
	reward_minutes INTEGER NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	answer_key JSON NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (reward_minutes >= 0 AND reward_minutes <= 120), 
	FOREIGN KEY(owner_id) REFERENCES users (id), 
	FOREIGN KEY(student_id) REFERENCES users (id), 
	FOREIGN KEY(classroom_id) REFERENCES classrooms (id)
);

CREATE INDEX ix_assignments_created_at ON assignments (created_at);

CREATE INDEX ix_assignments_owner_id ON assignments (owner_id);

CREATE INDEX ix_assignments_status ON assignments (status);

CREATE INDEX ix_assignments_student_id ON assignments (student_id);

CREATE TABLE blocked_app_rules (
	policy_id VARCHAR(36) NOT NULL, 
	package VARCHAR(200) NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (policy_id, package), 
	FOREIGN KEY(policy_id) REFERENCES device_policies (id)
);

CREATE INDEX ix_blocked_app_rules_created_at ON blocked_app_rules (created_at);

CREATE INDEX ix_blocked_app_rules_policy_id ON blocked_app_rules (policy_id);

CREATE TABLE classroom_members (
	classroom_id VARCHAR(36) NOT NULL, 
	student_id VARCHAR(36) NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (classroom_id, student_id), 
	FOREIGN KEY(classroom_id) REFERENCES classrooms (id), 
	FOREIGN KEY(student_id) REFERENCES users (id)
);

CREATE INDEX ix_classroom_members_classroom_id ON classroom_members (classroom_id);

CREATE INDEX ix_classroom_members_created_at ON classroom_members (created_at);

CREATE INDEX ix_classroom_members_student_id ON classroom_members (student_id);

CREATE TABLE reading_plans (
	book_id VARCHAR(36) NOT NULL, 
	student_id VARCHAR(36) NOT NULL, 
	assigned_by VARCHAR(36) NOT NULL, 
	classroom_id VARCHAR(36), 
	start_page INTEGER NOT NULL, 
	end_page INTEGER NOT NULL, 
	reward_minutes INTEGER NOT NULL, 
	pass_percent INTEGER NOT NULL, 
	auto_reward BOOLEAN NOT NULL, 
	reward_guardian_id VARCHAR(36), 
	active BOOLEAN NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (start_page > 0 AND end_page >= start_page), 
	CHECK (reward_minutes >= 0 AND reward_minutes <= 30 AND pass_percent >= 50 AND pass_percent <= 100), 
	FOREIGN KEY(book_id) REFERENCES study_books (id), 
	FOREIGN KEY(student_id) REFERENCES users (id), 
	FOREIGN KEY(assigned_by) REFERENCES users (id), 
	FOREIGN KEY(classroom_id) REFERENCES classrooms (id), 
	FOREIGN KEY(reward_guardian_id) REFERENCES users (id)
);

CREATE INDEX ix_reading_plans_assigned_by ON reading_plans (assigned_by);

CREATE INDEX ix_reading_plans_book_id ON reading_plans (book_id);

CREATE INDEX ix_reading_plans_created_at ON reading_plans (created_at);

CREATE INDEX ix_reading_plans_student_id ON reading_plans (student_id);

CREATE TABLE quizzes (
	owner_id VARCHAR(36) NOT NULL, 
	assignment_id VARCHAR(36) NOT NULL, 
	title VARCHAR(150) NOT NULL, 
	time_limit_seconds INTEGER NOT NULL, 
	validated BOOLEAN NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(owner_id) REFERENCES users (id), 
	UNIQUE (assignment_id), 
	FOREIGN KEY(assignment_id) REFERENCES assignments (id)
);

CREATE INDEX ix_quizzes_created_at ON quizzes (created_at);

CREATE INDEX ix_quizzes_owner_id ON quizzes (owner_id);

CREATE TABLE reading_attempts (
	plan_id VARCHAR(36) NOT NULL, 
	lesson_id VARCHAR(36) NOT NULL, 
	student_id VARCHAR(36) NOT NULL, 
	lesson_version INTEGER NOT NULL, 
	questions JSON NOT NULL, 
	answer_key JSON NOT NULL, 
	answers JSON NOT NULL, 
	result JSON NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	finished_at TIMESTAMP WITHOUT TIME ZONE, 
	start_key VARCHAR(100) NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (student_id, start_key), 
	FOREIGN KEY(plan_id) REFERENCES reading_plans (id), 
	FOREIGN KEY(lesson_id) REFERENCES book_lessons (id), 
	FOREIGN KEY(student_id) REFERENCES users (id)
);

CREATE INDEX ix_reading_attempts_created_at ON reading_attempts (created_at);

CREATE INDEX ix_reading_attempts_lesson_id ON reading_attempts (lesson_id);

CREATE INDEX ix_reading_attempts_plan_id ON reading_attempts (plan_id);

CREATE INDEX ix_reading_attempts_student_id ON reading_attempts (student_id);

CREATE TABLE reading_progress (
	plan_id VARCHAR(36) NOT NULL, 
	page_number INTEGER NOT NULL, 
	reported_seconds INTEGER NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (plan_id, page_number), 
	CHECK (reported_seconds >= 0 AND reported_seconds <= 86400), 
	FOREIGN KEY(plan_id) REFERENCES reading_plans (id)
);

CREATE INDEX ix_reading_progress_created_at ON reading_progress (created_at);

CREATE INDEX ix_reading_progress_plan_id ON reading_progress (plan_id);

CREATE TABLE submissions (
	assignment_id VARCHAR(36) NOT NULL, 
	student_id VARCHAR(36) NOT NULL, 
	text TEXT NOT NULL, 
	answers JSON NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	idempotency_key VARCHAR(100) NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (student_id, idempotency_key), 
	FOREIGN KEY(assignment_id) REFERENCES assignments (id), 
	FOREIGN KEY(student_id) REFERENCES users (id)
);

CREATE INDEX ix_submissions_assignment_id ON submissions (assignment_id);

CREATE INDEX ix_submissions_created_at ON submissions (created_at);

CREATE INDEX ix_submissions_student_id ON submissions (student_id);

CREATE TABLE assignment_attachments (
	assignment_id VARCHAR(36) NOT NULL, 
	uploader_id VARCHAR(36) NOT NULL, 
	submission_id VARCHAR(36), 
	filename VARCHAR(180) NOT NULL, 
	storage_key VARCHAR(36) NOT NULL, 
	media_type VARCHAR(80) NOT NULL, 
	size INTEGER NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(assignment_id) REFERENCES assignments (id), 
	FOREIGN KEY(uploader_id) REFERENCES users (id), 
	FOREIGN KEY(submission_id) REFERENCES submissions (id), 
	UNIQUE (storage_key)
);

CREATE INDEX ix_assignment_attachments_assignment_id ON assignment_attachments (assignment_id);

CREATE INDEX ix_assignment_attachments_created_at ON assignment_attachments (created_at);

CREATE INDEX ix_assignment_attachments_submission_id ON assignment_attachments (submission_id);

CREATE TABLE quiz_attempts (
	quiz_id VARCHAR(36) NOT NULL, 
	student_id VARCHAR(36) NOT NULL, 
	answers JSON NOT NULL, 
	score INTEGER, 
	completed_at TIMESTAMP WITHOUT TIME ZONE, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (quiz_id, student_id), 
	FOREIGN KEY(quiz_id) REFERENCES quizzes (id), 
	FOREIGN KEY(student_id) REFERENCES users (id)
);

CREATE INDEX ix_quiz_attempts_created_at ON quiz_attempts (created_at);

CREATE INDEX ix_quiz_attempts_quiz_id ON quiz_attempts (quiz_id);

CREATE INDEX ix_quiz_attempts_student_id ON quiz_attempts (student_id);

CREATE TABLE quiz_questions (
	quiz_id VARCHAR(36) NOT NULL, 
	position INTEGER NOT NULL, 
	prompt TEXT NOT NULL, 
	options JSON NOT NULL, 
	answer VARCHAR(500) NOT NULL, 
	explanation TEXT NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (quiz_id, position), 
	FOREIGN KEY(quiz_id) REFERENCES quizzes (id)
);

CREATE INDEX ix_quiz_questions_created_at ON quiz_questions (created_at);

CREATE INDEX ix_quiz_questions_quiz_id ON quiz_questions (quiz_id);

CREATE TABLE submission_reviews (
	submission_id VARCHAR(36) NOT NULL, 
	reviewer_id VARCHAR(36), 
	decision VARCHAR(30) NOT NULL, 
	feedback TEXT NOT NULL, 
	metadata_json JSON NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(submission_id) REFERENCES submissions (id), 
	FOREIGN KEY(reviewer_id) REFERENCES users (id)
);

CREATE INDEX ix_submission_reviews_created_at ON submission_reviews (created_at);

CREATE INDEX ix_submission_reviews_submission_id ON submission_reviews (submission_id);
