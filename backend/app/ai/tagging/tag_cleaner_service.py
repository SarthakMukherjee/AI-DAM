class TagCleanerService:

    @staticmethod
    def clean_tags(tags):

        cleaned_tags = []

        if not tags:
            return []

        for tag in tags:

            # -----------------------------------
            # HANDLE NESTED LISTS
            # -----------------------------------

            if isinstance(tag, list):

                for nested_tag in tag:

                    if isinstance(
                        nested_tag,
                        str
                    ):

                        normalized = (
                            nested_tag
                            .strip()
                            .lower()
                        )

                        if (
                            normalized
                            and normalized
                            not in cleaned_tags
                        ):
                            cleaned_tags.append(
                                normalized
                            )

                continue

            # -----------------------------------
            # HANDLE DICTIONARIES
            # -----------------------------------

            if isinstance(tag, dict):

                value = tag.get("tag")

                if isinstance(value, str):

                    normalized = (
                        value
                        .strip()
                        .lower()
                    )

                    if (
                        normalized
                        and normalized
                        not in cleaned_tags
                    ):
                        cleaned_tags.append(
                            normalized
                        )

                continue

            # -----------------------------------
            # HANDLE NORMAL STRINGS
            # -----------------------------------

            if isinstance(tag, str):

                normalized = (
                    tag
                    .strip()
                    .lower()
                )

                if (
                    normalized
                    and normalized
                    not in cleaned_tags
                ):
                    cleaned_tags.append(
                        normalized
                    )

        return cleaned_tags