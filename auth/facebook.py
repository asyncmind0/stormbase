FACEBOOK_NORMAL_PERMISSIONS = [
    # Provides access to the "About Me" section of the profile in the about
    # property
    "user_about_me",
    "friends_about_me",
    # Provides access to the user's list of activities as the activities
    # connection
    "user_activities",
    "friends_activities",
    # Provides access to the birthday with year as the birthday_date property
    "user_birthday",
    "friends_birthday",
    # Provides read access to the authorized user's check-ins or a friend's
    # check-ins that the user can see.
    "user_checkins",
    "friends_checkins",
    # Provides access to education history as the education property
    "user_education_history",
    "friends_education_history",
    # Provides access to the list of events the user is attending as the
    # events connection
    "user_events",
    "friends_events",
    # Provides access to the list of groups the user is a member of as the
    # groups connection
    "user_groups",
    "friends_groups",
    # Provides access to the user's hometown in the hometown property
    "user_hometown",
    "friends_hometown",
    # Provides access to the user's list of interests as the interests
    # connection
    "user_interests",
    "friends_interests",
    # Provides access to the list of all of the pages the user has liked as
    # the likes connection
    "user_likes",
    "friends_likes",
    # Provides access to the user's current location as the location property
    "user_location",
    "friends_location",
    # Provides access to the user's notes as the notes connection
    "user_notes",
    "friends_notes",
    # Provides access to the user's online/offline presence
    "user_online_presence",
    "friends_online_presence",
    # Deprecated; not supported after November 22, 2011. Provides access to
    # the photos and videos the user has uploaded, and photos and videos the
    # user has been tagged in; this permission is equivalent to requesting
    # both user_photos and user_videos, or friends_photos and friends_videos.
    "user_photo_video_tags",
    "friends_photo_video_tags",
    # Provides access to the photos the user has uploaded, and photos the user
    # has been tagged in
    "user_photos",
    "friends_photos",
    # Provides access to the questions the user or friend has asked
    "user_questions",
    "friends_questions",
    # Provides access to the user's family and personal relationships and
    # relationship status
    "user_relationships",
    "friends_relationships",
    # Provides access to the user's relationship preferences
    "user_relationship_details",
    "friends_relationship_details",
    # Provides access to the user's religious and political affiliations
    "user_religion_politics",
    "friends_religion_politics",
    # Provides access to the user's most recent status message
    "user_status",
    "friends_status",
    # Provides access to the videos the user has uploaded, and videos the user
    # has been tagged in
    "user_videos",
    "friends_videos",
    # Provides access to the user's web site URL
    "user_website",
    "friends_website",
    # Provides access to work history as the work property
    "user_work_history",
    "friends_work_history",
    "email"
]

EXTENDED_PERMISSIONS = [
    # Provides access to any friend lists the user created. All user's friends
    # are provided as part of basic data, this extended permission grants
    # access to the lists of friends a user has created, and should only be
    # requested if your application utilizes lists of friends.",
    "read_friendlists",
    # Provides read access to the Insights data for pages, applications, and
    # domains the user owns.
    "read_insights",
    # Provides the ability to read from a user's Facebook Inbox.",
    "read_mailbox",
    # Provides read access to the user's friend requests
    "read_requests",
    # Provides access to all the posts in the user's News Feed and enables
    # your application to perform searches against the user's News Feed
    "read_stream",
    # Provides applications that integrate with Facebook Chat the ability to
    # log in users.
    "xmpp_login",
    # Provides the ability to manage ads and call the Facebook Ads API on
    # behalf of a user.
    "ads_management",
    # Enables your application to create and modify events on the user's behalf
    "create_event",
    # Enables your app to create and edit the user's friend lists.
    "manage_friendlists",
    # Enables your app to read notifications and mark them as read. This
    # permission will be required to all access to notifications after October
    # 22, 2011.
    "manage_notifications",
    # Enables your app to perform authorized requests on behalf of the user at
    # any time. By default, most access tokens expire after a short time
    # period to ensure applications only make requests on behalf of the user
    # when the are actively using the application. This permission makes the
    # access token returned by our OAuth endpoint long-lived.
    "offline_access",
    # Enables your app to perform checkins on behalf of the user.
    "publish_checkins",
    # Enables your app to post content, comments, and likes to a user's stream
    # and to the streams of the user's friends. With this permission, you can
    # publish content to a user's feed at any time, without requiring
    # offline_access. However, please note that Facebook recommends a user-
    # initiated sharing model.
    "publish_stream",
    # Enables your application to RSVP to events on the user's behalf
    "rsvp_event",
    # Enables your application to send messages to the user and respond to
    # messages from the user via text message
    "sms",
    # Enables your application to publish user scores and achievements.
    "publish_actions",
    # Enables your application to retrieve access_tokens for pages the user
    # administrates. The access tokens can be queried using the "accounts"
    # connection in the Graph API. This permission is only compatible with the
    # Graph API.
    "manage_pages"
]

TBL_USER_FIELDS = [
    "uid",  # int	The user ID of the user being queried.
    "username",  # string	The username of the user being queried.
    "first_name",  # string	The first name of the user being queried.
    "middle_name",  # string	The middle name of the user being queried.
    "last_name",  # string	The last name of the user being queried.
    "name",  # string	The full name of the user being queried.
    "pic_small",  # string	The URL to the small-sized profile picture for the user being queried. The image can have a maximum width of 50px and a maximum height of 150px. This URL may be blank.
    "pic_big",  # string	The URL to the largest-sized profile picture for the user being queried. The image can have a maximum width of 200px and a maximum height of 600px. This URL may be blank.
    "pic_square",  # string	The URL to the square profile picture for the user being queried. The image can have a maximum width and height of 50px. This URL may be blank.
    "pic",  # string	The URL to the medium-sized profile picture for the user being queried. The image can have a maximum width of 100px and a maximum height of 300px. This URL may be blank.
    "affiliations",  # array	The networks to which the user being queried belongs. The status field within this field will only return results in English.
    "profile_update_time",  # time	The time the profile of the user being queried was most recently updated. If the user's profile has not been updated in the past three days, this value will be 0.
    "timezone",  # int	The user's timezone offset from UTC.
    "religion",  # string	The religion of the user being queried.
    "birthday",  # string	The birthday of the user being queried. The format of this date varies based on the user's locale.
    "birthday_date",
    # string	The birthday of the user being queried in MM/DD/YYYY format.
    "sex",  # string	The gender of the user being queried.
    "hometown_location",
            # array	The hometown (and state) of the user being queried.
    "meeting_sex",  # array	A list of the genders the person the user being queried wants to meet.
    "meeting_for",  # array	A list of the reasons the user being queried wants to meet someone.
    "relationship_status",
            # string	The type of relationship for the user being queried.
    "significant_other_id",  # uid	The user ID of the partner (for example, husband, wife, boyfriend, girlfriend) of the user being queried.
    "political",  # string	The political views of the user being queried.
    "current_location",
            # array	The current location of the user being queried.
    "activities",  # string	The activities of the user being queried.
    "interests",  # string	The interests of the user being queried.
    "is_app_user",  # bool	Indicates whether the user being queried has logged in to the current application.
    "music",  # string	The favorite music of the user being queried.
    "tv",
            # string	The favorite television shows of the user being queried.
    "movies",  # string	The favorite movies of the user being queried.
    "books",  # string	The favorite books of the user being queried.
    "quotes",  # string	The favorite quotes of the user being queried.
    "about_me",  # string	More information about the user being queried.
    "hs_info",  # array	Deprecated. This value is now equivalent to education entry of type ''High School''.
    "education_history",  # array	Deprecated. This value is now equivalent to education entry of type ''College''.
    "work_history",
            # array	Deprecated. This value is now equivalent to work.
    "notes_count",
            # int	The number of notes created by the user being queried.
    "wall_count",
            # int	The number of Wall posts for the user being queried.
    "status",  # string	The current status of the user being queried.
    "has_added_app",
            # bool	Deprecated. This value is now equivalent to is_app_user.
    "online_presence",  # string	The user's Facebook Chat status. Returns a string, one of active, idle, offline, or error (when Facebook can't determine presence information on the server side). The query does not return the user's Facebook Chat status when that information is restricted for privacy reasons.
    "locale",  # string	The two-letter language code and the two-letter country code representing the user's locale. Country codes are taken from the ISO 3166 alpha 2 code list.
    "proxied_email",  # string	The proxied wrapper for a user's email address. If the user shared a proxied email address instead of his or her primary email address with you, this address also appears in the email field (see above). Facebook recommends you query the email field to get the email address shared with your application.
    "profile_url",  # string	The URL to a user's profile. If the user specified a username for his or her profile, profile_url contains the username.
    "email_hashes",  # array	An array containing a set of confirmed email hashes for the user. Emails are registered via the deprecated connect.registerUsers API call and are only confirmed when the user adds your application. The format of each email hash is the crc32 and md5 hashes of the email address combined with an underscore (_).
    "pic_small_with_logo",  # string	The URL to the small-sized profile picture for the user being queried. The image can have a maximum width of 50px and a maximum height of 150px, and is overlaid with the Facebook favicon. This URL may be blank.
    "pic_big_with_logo",  # string	The URL to the largest-sized profile picture for the user being queried. The image can have a maximum width of 200px and a maximum height of 600px, and is overlaid with the Facebook favicon. This URL may be blank.
    "pic_square_with_logo",  # string	The URL to the square profile picture for the user being queried. The image can have a maximum width and height of 50px, and is overlaid with the Facebook favicon. This URL may be blank.
    "pic_with_logo",  # string	The URL to the medium-sized profile picture for the user being queried. The image can have a maximum width of 100px and a maximum height of 300px, and is overlaid with the Facebook favicon. This URL may be blank.
    "allowed_restrictions",  # string	A comma-delimited list of Demographic Restrictions types a user is allowed to access. Currently, alcohol is the only type that can get returned.
    "verified",
            # bool	Indicates whether or not Facebook has verified the user.
    "profile_blurb",  # string	This string contains the contents of the text box under a user's profile picture.
    "family",  # array	Note: For family information, you should query the family FQL table instead.

    # This array contains a series of entries for the immediate relatives of
    # the user being queried. Each entry is also an array containing the
    # following fields:

    # relationship -- A string describing the type of relationship. Can be one of parent, mother, father, sibling, sister, brother, child, son, daughter.
    # uid (optional) -- The user ID of the relative, which gets displayed if the account is linked to (confirmed by) another account. If the relative did not confirm the relationship, the name appears instead.
    # name (optional) -- The name of the relative, which could be text the user entered. If the relative confirmed the relationship, the uid appears instead.
    # birthday -- If the relative is a child, this is the birthday the user
    # entered.

    # Note: At this time, you cannot query for a specific relationship (like
    # SELECT family FROM user WHERE family.relationship = 'daughter' AND uid =
    # '$x'); you'll have to query on the family field and filter the results
    # yourself.
    "website",  # string	The website of the user being queried.
    "is_blocked",  # bool	Returns true if the user is blocked to the viewer/logged in user.
    "contact_email",  # string	A string containing the user's primary Facebook email address. If the user shared his or her primary email address with you, this address also appears in the email field (see below). Facebook recommends you query the email field to get the email address shared with your application.
    "email",  # string	A string containing the user's primary Facebook email address or the user's proxied email address, whichever address the user granted your application. Facebook recommends you query this field to get the email address shared with your application.
    "third_party_id",  # string	A string containing an anonymous, but unique identifier for the user. You can use this identifier with third-parties.
    "name_format",  # string	The user's name formatted to correctly handle Chinese, Japanese, Korean ordering.
    "video_upload_limits",  # array	The size of the video file and the length of the video that a user can upload. This object contains length and size of video.
    "games",  # string	The user's favorite games; this field is deprecated and will be removed in the near future. The string is a comma-separated list.
    "is_minor",  # bool	Whether or not the user is a minor.
    "work",  # array	A list of the user's work history. Contains employer, location, position, start_date and end_date fields.
    "education",  # array	A list of the user's education history. Contains year and type fields, and school object (name, id, type, and optional year, degree, concentration array, classes array, and with array ).
    "sports",  # array	The sports that the user plays. The array objects contain id and name fields.
    "favorite_athletes",  # array	The user's favorite athletes; this field is deprecated and will be removed in the near future. The array objects contain id and name fields.
    "favorite_teams",  # array	The user's favorite teams; this field is deprecated and will be removed in the near future. The array objects contain id and name fields.
    "inspirational_people",  # array	The people who inspire the user. The array objects contain id and name fields.
    "languages",  # array	The user's languages. The array objects contain id and name fields.
    "likes_count",  # int	Count of all the pages this user has liked.
    "friend_count",  # int	Count of all the user's friends.
    "mutual_friend_count",  # int	The number of mutual friends shared by the user in the query and the session user.
    "can_post",
            # bool	Whether or not the viewer can post to the user's Wall.
]

FRIEND_MANAGER_PERMISSIONS = [
    "read_friendlists",
    "manage_friendlists",
    "user_location",
    "friends_location"
]
