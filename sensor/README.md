## Visualisation of procedures

![image](https://github.com/tum-esm/hermes/assets/59452158/a87f1974-4448-4a35-bfbc-3481af7e181c)


## System release & update process

1. Create a new release
   1. Merge all changes into the `main` branch
   2. Check whether the GitHub CI tests were successful for this commit
   3. Tag the commit as `v0.1.0-beta.3` (or whatever the new version is)
   4. Create a release on GitHub with the same tag (`v0.1.0-beta.3`)
   5. Write release notes


2. Update the `config.json` that is sent to the system
    ```json
    {
        "version": "0.1.0-beta.3",
        ...
    }
    ```

3. Wait for the system to confirm the update with new revision

